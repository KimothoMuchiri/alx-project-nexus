import requests
from django_ip_geolocation.backends.base import GeolocationBackend


class IPinfoLiteBackend(GeolocationBackend):
    """
    Custom backend for django-ip-geolocation that talks to IPinfo Lite.

    IPinfo Lite docs: https://ipinfo.io/developers/lite-api
    """

    
    API_URL = "https://ipinfo.io/{ip}/lite"

    def geolocate(self):
        """
        Call IPinfo Lite for this IP, store response in _raw_data,
        and return parsed data dict (via base .data()).
        """
        url = self.API_URL.format(ip=self._ip or "")

        try:
            resp = requests.get(url, timeout=2)
            resp.raise_for_status()
            self._raw_data = resp.json()
        except Exception:
            # On failure, keep _raw_data empty; base .data() will still return a dict
            self._raw_data = {}

        return self.data()

    def _parse(self):
        """
        Parse _raw_data into _continent, _country, _geo_data.

        IPinfo Lite typical fields:
          - ip
          - country        (e.g. "Kenya")
          - country_code   (e.g. "KE"), depending on plan
          - continent
          - continent_code
        """
        if not self._raw_data:
            self._continent = None
            self._country = None
            self._geo_data = None
            return

        # Map raw data to the fields django-ip-geolocation expects
        continent = self._raw_data.get("continent") or self._raw_data.get("continent_name")
        country = self._raw_data.get("country") or self._raw_data.get("country_name")

        self._continent = continent
        self._country = country

        # Store the full geo info in _geo_data (you can shape this however you like)
        self._geo_data = {
            "ip": self._raw_data.get("ip"),
            "country": country,
            "continent": continent,
            "country_code": self._raw_data.get("country_code"),
            "continent_code": self._raw_data.get("continent_code"),
        }