# Copyright (c) 2021, Cisco Systems, Inc. and/or its affiliates
# Licensed under the MIT License, see the "LICENSE" file accompanying this file.

import base64
import requests
from .version import __version__

__all__ = ('Postback', 'Client', '__version__')


class Postback(object):
    def __init__(
        self,
        webhookid="",
        URL="",
        token="",
        fingerprint="",
        format="",
        bucket="",
        region="",
        accesskey="",
        secretkey=""
    ):
        self.webhookid = webhookid
        self.URL = URL
        self.token = token
        self.fingerprint = fingerprint
        self.format = format
        self.bucket = bucket
        self.region = region
        self.accesskey = accesskey
        self.secretkey = secretkey

    def validate(self):
        if self.webhookid != "":
            return True

        if self.format != "" and self.format != "ctim" and self.format != "splunk" and self.format != "s3":
            return False

        if self.format != "ctim" and self.URL == "":
            return False

        if self.format == "splunk" and self.token == "":
            return False

        if self.format == "s3" and (
            self.bucket == "" or self.region == "" or self.accesskey == "" or self.secretkey == ""
        ):
            return False

        return True

    def parse(self, data):
        # <URL> [token [fingerprint [format [bucket region accesskey secretkey]]]]
        tokens = data.split(" ")
        if len(tokens) > 8:
            return False

        for i, token in enumerate(tokens):
            if token == "''" or token == '""':
                tokens[i] = ""

        if len(tokens) == 8:
            self.URL = tokens[0]
            self.token = tokens[1]
            self.fingerprint = tokens[2]
            self.format = tokens[3]
            self.bucket = tokens[4]
            self.region = tokens[5]
            self.accesskey = tokens[6]
            self.secretkey = tokens[7]
            return self.validate()

        if len(tokens) > 4:
            return False

        if len(tokens) == 4:
            self.URL = tokens[0]
            self.token = tokens[1]
            self.fingerprint = tokens[2]
            self.format = tokens[3]
            return self.validate()

        if len(tokens) == 3:
            self.URL = tokens[0]
            self.token = tokens[1]
            self.fingerprint = tokens[2]
            return self.validate()

        if len(tokens) == 2:
            self.URL = tokens[0]
            self.token = tokens[1]
            return self.validate()

        if len(tokens) == 1:
            self.URL = tokens[0]
            return self.validate()

        return False


class Client(object):
    """
    Python wrapper of the Orbital public API.
    """

    def __init__(self, host, insecure, token="", verbose=False):
        # Create an Orbital client.
        # host is the ip:port of the Orbital service.
        # insecure is true/false, and determines whether the server certificate validation can be skipped.
        # token is the access token obtained by calling login.
        # verbose is true/false, and enables printing debug information to the console about request status,
        # headers, and body.
        self.host = host
        self.verify = not insecure
        self.token = token
        self.verbose = verbose

    def get_url(self, operation, uid="", uid2=""):
        # get_url contains the path of all supported API endpoints.
        urls = {
            "logon":         "/v0/oauth2/token",
            "ok":            "/v0/ok",
            "probe":         "/v0/probe",
            "query_create":  "/v0/query",
            "query_disable": "/v0/query/%s" % uid,
            "results":       "/v0/jobs/%s/results" % uid,
            "stock":         "/v0/stock",
            "webhook_post":  "/v0/webhooks",
            "webhook_patch": "/v0/webhooks/" + uid,
            "webhook_get":   "/v0/webhooks/" + uid,
            "webhook_list":  "/v0/webhooks",
            "webhook_sendresult":  "/v0/webhooks/" + uid + "/results/" + uid2,
            "features_get":  "/v0/features/" + uid,
            "features_list": "/v0/features",
        }

        url = urls.get(operation, "")
        if url == "":
            raise("unexpected operation")

        return self.host + url

    def _req(self, verb, url, data=None, params=None):
        r = requests.request(verb,
                             url,
                             json=data or {},
                             params=params or {},
                             verify=self.verify,
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.token})
        if self.verbose:
            print("data:%s, params:%s, status code:%s, headers:%s, body:%s" %
                  (data, params, r.status_code, r.headers, r.text))
        return r

    def login(self, apikey):
        # login gets an access token for a client id and password.
        r = requests.request(
            "POST",
            self.get_url("logon"),
            verify=self.verify,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Basic " + base64.standard_b64encode(bytearray(apikey, 'utf-8')).decode("utf-8")
            }
        )
        if self.verbose:
            print("status code: %s, headers: %s, body: %s" %
                  (r.status_code, r.headers, r.text))
        return r.json()

    def ok(self):
        # ok gets the login information associated with the access token, and also serves as a health check for the
        # service.
        r = self._req("GET", self.get_url("ok"))
        return r.json()

    def probe(self, queries, seconds=60, nodes=None, os=None, stock="", stockargs=None):
        # Probe submits the provided queries, and synchronously return results from any selected, connected nodes that
        # occur within the expiration time.
        #
        # Queries is a required list of { "sql": <sql>, "label":<optional label>, "name":<optional name>}
        #
        # Seconds is the unix epoch time when the probe expires
        #
        # Nodes is an optional list of node id's, or ["all"] and determines which nodes to send the queries.
        # Defaults to all.
        #
        # Os is an optional list of os's: "windows", "linux", "darwin", which will filter the nodes based on their
        # os, when supplied.
        #
        # Stock is an identifier for an item in the stock query catalog
        #
        # Stockargs is a map of key value pairs that are associated with the chosen stock query
        data = {
            "expiry": seconds,
            "nodes": nodes or [],
            "os": os or [],
            "osQuery": queries,
            "stock": stock,
            "stockargs": stockargs or {},
        }
        r = self._req("POST", self.get_url("probe"), data)
        return r.json()

    def query_disable(self, query_id):
        # disables a query with the given id.
        r = self._req("DELETE", self.get_url("query_disable", query_id))
        return r.status_code

    def query_create(
        self, queries, interval,
        seconds=60,
        nodes=None,
        os=None,
        postbacks=None,
        stock="",
        stockargs=None,
        context=None,
    ):
        # See the probe method for arguments.
        #
        # Postbacks specifies a list, where each entry must contain either a valid webhook id or url, where results
        # for the specified query will be sent. The webhook must be accessible by the Orbital cloud at the time of
        # your request.  Postbacks have the form:
        #
        #   {
        #     url: <url of the callback>,
        #     webhookid: <id of a saved webhook>,
        #     fingerprint: <optional fingerprint to verify server cert>,
        #     token: <optional bearer token to present to webhook host>
        #   }
        #
        # Context is a map of arbitrary key value pairs that will be returned with results for the queries associated
        # with this request.
        data = {
            "interval": interval,
            "expiry": seconds,
            "nodes": nodes or [],
            "os": os or [],
            "postbacks": postbacks or [],
            "osQuery": queries,
            "stock": stock,
            "stockargs": stockargs or {},
            "context": context or {}
        }
        r = self._req("POST", self.get_url("query_create"), data)
        return r.json()

    def results(self, jobid, cursor=""):
        # results gets the results for a specific job, optionally starting at a cursor returned from a previous call.
        # jobid is an id returned from query.
        # cursor is the "next" value returned from a previous results call
        params = {}
        if cursor != "":
            params["cursor"] = cursor
        r = self._req("GET", self.get_url("results", jobid), params=params)
        return r.json()

    def stock(self):
        # stock returns information about the stock catalog.
        r = self._req("GET", self.get_url("stock"))
        return r.json()

    def webhook_create(
        self, disabled, url,
        token="",
        fingerprint="",
        label="",
        format="",
        bucket="",
        region="",
        accesskey="",
        secretkey="",
    ):
        # webhook_create creates a named webhook, usable by any user in the organization of the access token
        # disabled specifies whether the initial state of the webhook is disabled
        # url is the required protocol, host, path, and query args for the callback, which must be callable
        #   at the time of creation, for any format other than "ctim."
        # token is an optional bearer token to present to the webhook, or splunk token.
        # fingerprint is an optional fingerprint used to validate the server certificate
        # label is an optional label to associate with the webhook
        # format is the custom format of the destination, which can be left blank, or "ctim," "splunk," or "s3."
        # bucket is the bucket name for the s3 format
        # region is the region name for the s3 format
        # accesskey is the Access Key for the bucket in the s3 format
        # secretkey is the Secret Key for the bucket in the s3 format
        data = {
            "disabled":        disabled,
            "config": {
                "url":         url,
                "token":       token,
                "fingerprint": fingerprint,
                "label":       label,
                "format":      format,
                "bucket":      bucket,
                "region":      region,
                "accesskey":   accesskey,
                "secretkey":   secretkey
            },
        }
        r = self._req("POST", self.get_url("webhook_post"), data)
        return r.json()

    def webhook_update(
        self, wid,
        disabled=False,
        url="",
        token="",
        fingerprint="",
        label="",
        format="",
        bucket="",
        region="",
        accesskey="",
        secretkey="",
    ):
        # webhook_update updates an existing named webhook, replacing all fields.
        # wid is the id of the webhook
        # see webhook_create for descriptions of other fields.
        data = {
            "id": wid,
            "disabled":        disabled,
            "config": {
                "url":         url,
                "token":       token,
                "fingerprint": fingerprint,
                "label":       label,
                "format":      format,
                "bucket":      bucket,
                "region":      region,
                "accesskey":   accesskey,
                "secretkey":   secretkey
            },
        }
        r = self._req("PATCH", self.get_url("webhook_patch", wid), data)
        return r.json()

    def webhook_get(self, wid):
        # webhook_get gets the webhook with the specified id
        # wid is the id of an existing webhook
        r = self._req("GET", self.get_url("webhook_get", wid))
        return r.json()

    def webhook_list(self):
        # webhook_list returns all webhooks in the organization specified by the access token
        r = self._req("GET", self.get_url("webhook_list"))
        return r.json()

    def webhook_sendresult(self, webhookID, resultID):
        # webhook_sendresult sends an existing results to an existing webhook
        r = self._req("POST", self.get_url("webhook_sendresult", webhookID, resultID))
        return r.json()

    def features_get(self, fid):
        # features_get gets the features with the specified id
        # wid is the id of an existing features
        r = self._req("GET", self.get_url("features_get", fid))
        return r.json()

    def features_list(self):
        # features_list returns all features in the organization specified by the access token
        r = self._req("GET", self.get_url("features_list"))
        return r.json()
