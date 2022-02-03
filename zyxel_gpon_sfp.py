import fire
import requests
import random
import demjson
from binascii import hexlify


def is_hex(a):
    """ checks if a is a properly formated hex string """
    try:
        int(a, 16)  # Just check if we can properly parse the hex
        return len(a) % 2 == 0  # We're dealing with strings hex encoded
    except ValueError:
        return False


class SFP:
    def __init__(self, sfp_addr, username="admin", password="1234"):
        self._sfp_addr = sfp_addr
        self._user = username
        self._pass = password

    def _req(self, path, method="GET", headers={}):
        """ Helper to perform request on the SFPs HTTP API """
        full_path = f"{self._sfp_addr}{path}"
        auth = (self._user, self._pass)

        if method == "GET":
            return requests.get(full_path, auth=auth, headers=headers)
        elif method == "POST":
            return requests.post(full_path, auth=auth, headers=headers)

    def info(self):
        resp_sn = self._req(path="/cgi/get_sn")
        resp_gpon = self._req(path="/cgi/get_gpon_info")

        # WARNING: This is a javascript object, not JSON...
        test = demjson.decode(resp_sn.text) | demjson.decode(resp_gpon.text)

        return test

    def set_slid(self, slid, string=False):
        # Transform to a valid parameter
        _slid = hexlify(slid).decode(
            "ascii").lower() if string else slid.lower()

        if not is_hex(_slid):
            return f"[!] Invalid SLID `{_slid}` (HEX)"

        print(f"[ ] Applying SLID `{_slid}` (HEX)")
        resp = self._req(
            path=f"/cgi/set_sn?mode=1&pass={_slid}", method="POST")
        if resp.status_code == 200 and resp.text == "1":
            return f"[+] Applied SLID `{_slid}`, a reboot of the SFP is required."

    def set_sn(self, sn, string):
        return "Untested"
        # _sn = hexlify(sn) if string else sn
        # f not is_hex(_sn):
        #     return f"[!] Invalid SN `{_sn}` (HEX)"

        # print(f"[ ] Applying SN `{_sn}` (HEX)")
        # resp = self._req(path=f"/cgi/set_sn?mode=1?sn={sn}", method="POST")
        # if resp.status_code == 200 and resp.text == "1":
        #     return f"[+] Applied SN `{_sn}`, a reboot of the SFP is required."


if __name__ == "__main__":
    fire.Fire(SFP)
