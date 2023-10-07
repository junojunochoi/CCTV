import json
import requests

import folium
import geopandas as gpd
from owslib.wfs import WebFeatureService

from vworld import VWORLD_API_KEY

url = 'https://geo.safemap.go.kr/geoserver/safemap/wms?'
wfs = WebFeatureService(url=url)
params = dict(service='wfs', version='1.1.1', typeName='safemap:A2SM_CRMNLSTATS',
              request='GetFeature', outputFormat='application/json')           
q = requests.Request('GET', url, params=params).prepare().url
data = gpd.read_file(q)

seoul = data.loc[data['CTPRVN_CD']=='11']

def get_emdcode(p):
    apiurl = "https://api.vworld.kr/req/address?"
    params = {
        "service": "address",
        "request": "getaddress",
        "crs": "epsg:900913",
        "point": f"{p.x},{p.y}",
        "format": "json",
        "type": "parcel",
        "key": VWORLD_API_KEY,
        "simple": "true"
    }
    response = requests.get(apiurl, params=params)
    if response.status_code == 200:
        return response.json()['response']['result'][0]['structure']['level4L']
    return


seoul['dong'] = seoul['geometry'].apply(get_emdcode)

# 서울 행정구역 json raw파일(githubcontent)
r = requests.get('https://raw.githubusercontent.com/southkorea/seoul-maps/master/juso/2015/json/seoul_neighborhoods_geo.json')
# r = requests.get('https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-submunicipalities-2018-geo.json')
c = r.content
seoul_geo = json.loads(c)

# vworld api
vworld = folium.TileLayer(
        tiles=''.join([
            "http://api.vworld.kr/req/wmts/1.0.0/",
            VWORLD_API_KEY,     # VWorld API Key 
            "/Hybrid/{z}/{y}/{x}.png"
        ]),
        attr='Vworld',
        control=False
    )

# default start point 동국대
lat, lon = 37.5583, 127.0002
zoom_size = 13

# initialization
m = folium.Map(
    location=[lat, lon],
    zoom_start=zoom_size,
    tiles=vworld
)

folium.GeoJson(
    seoul_geo,
    style_function=lambda feature: {
        "fillColor": "transparent",
        "color": "black",
        "weight": 2,
        "dashArray": "5, 5",
    },
    name='행정동',
).add_to(m)

# layers = ['safemap:A2SM_CRMNLSTATS', 'safemap:A2SM_CRMNLHspot']
styles = ['Tot', 'Nrctc', 'Murder', 'Gamble', 'Brglr', 'Rape', 'Theft', 'Tmpt', 'Violn', 'Arson']
for s in styles:
    total = (s=='Tot')
    folium.raster_layers.WmsTileLayer(url = 'https://geo.safemap.go.kr/geoserver/safemap/wms?',
                                  layers = 'safemap:A2SM_CRMNLSTATS',
                                  styles = ''.join(['A2SM_CrmnlStats_', s]),
                                  transparent = True, 
                                  control = True,
                                  fmt="image/png",
                                  name = (s, 'Criminal stats')[total],
                                  overlay = True,
                                  show = False,
                                  ).add_to(m)

folium.Choropleth(
    geo_data=seoul_geo,
    name="지역별 범죄지수",
    data=seoul,
    columns=["dong", "TOT"],
    nan_fill_color="transparent",
    key_on="properties.EMD_KOR_NM",
    fill_color="YlOrRd",
    # bins=[1,2,3,4,5],
    fill_opacity=0.75,
    line_opacity=0.2,
    legend_name="Crime #",
    highlight=True,
).add_to(m)

folium.LayerControl().add_to(m)
m.save('crimeMap.html')