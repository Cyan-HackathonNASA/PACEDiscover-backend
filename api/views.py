from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers import ImageURLSerializer
import calendar
# import requests


class GetImageURLView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        serializer = ImageURLSerializer(data=request.query_params)

        if serializer.is_valid():
            url = self._generate_pace_url(serializer.validated_data)

            # response = requests.get(url)
            # if response.status_code == 404:
            #     return Response(status=status.HTTP_404_NOT_FOUND)

            return Response({"url": url}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_pace_url(self, data: dict) -> str | None:

        BASE_URL = 'https://oceancolor.gsfc.nasa.gov/showimages/PACE_OCI/IMAGES/'

        year = data.get('year')
        month = data.get('month')
        res = data.get("res")
        period = data.get('period')
        product = self._set_product(data.get('product'))

        if period == 'daily':
            day = data.get('day')
            return (f'{BASE_URL}{product[0]}/L3/{year}/{month}{day}/PACE_OCI.{year}{month}{day}.L3m.DAY.{product[1]}.V2_0.{product[2]}.{res}.NRT.nc.png')

        if period == 'monthly':
            _, last_day = calendar.monthrange(int(year), int(month))
            return f'{BASE_URL}{product[0]}/L3/{year}/{month}01/PACE_OCI.{year}{month}01_{year}{month}{last_day}.L3m.MO.{product[1]}.V2_0.{product[2]}.{res}.NRT.nc.png'

        if period == 'annual':
            return f'{BASE_URL}{product[0]}/L3/{year}/0101/PACE_OCI.{year}0101_{year}1231.L3m.YR.{product[1]}.{product[2]}.{res}.nc.png'

        raise ValueError("Invalid period provided.")

    def _set_product(self, product: str) -> tuple:
        match product:

            # AER_DB Group
            case '59,188':
                return 'AER_DB', 'AER_DBOCEAN', 'aot_1610_db'

            # CARBON Group
            case '64,255':
                return 'CARBON', 'CARBON', 'carbon_phyto'

            # CHL Group
            case '5,6':
                return 'CHL', 'CHL', 'chlor_a'

            # POC Group
            case '10,36':
                return 'POC', 'POC', 'poc'

            case _:
                raise ValueError("Invalid product code provided.")
