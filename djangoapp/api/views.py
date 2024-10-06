from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers import ImageSerializer, ChatMessageSerializer
import calendar
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import openai
import os
import json
import requests
import base64

CHAT_DIR = os.path.join(os.path.dirname(__file__), 'chats')
PROMPT = """You are an educational assistant focused exclusively on the PACE (Plankton, Aerosol, Cloud, ocean Ecosystem) mission. Your purpose is to provide accurate, comprehensive, and engaging information about PACE, emphasizing its scientific significance, objectives, and methodologies. Respond only to inquiries related to PACE and its associated topics, ensuring clarity and depth in your explanations.

Key areas to cover include:

    Overview of PACE:
        Define what PACE is and its importance in understanding ocean and atmospheric interactions.
        Explain the mission's goals and how it contributes to our knowledge of the Earth's climate and ecosystems.

    Fundamental Properties of Light:
        Describe the nature of light as both a particle (photon) and a wave, and explain the implications of this duality in scientific studies.
        Discuss the electromagnetic spectrum, focusing on the visible light range and its relevance to PACE.

    Light Behavior:
        Explain how light moves and behaves when it interacts with different mediums, including transmission, absorption, scattering, reflection, refraction, and diffraction.
        Highlight how these interactions affect the measurements taken by PACE.

    Types of Scattering:
        Detail the different types of scattering (Rayleigh and Mie) and their significance in atmospheric science and remote sensing.
        Provide examples of how scattering influences observations of the sky and climate.

    Rainbows and Light Dispersion:
        Explain the science behind rainbows, including the processes of refraction and dispersion that occur within raindrops.
        Discuss the implications of this phenomenon for understanding light interactions in the atmosphere.

    PACE’s Technology and Instruments:
        Describe the advanced instruments and technologies used by PACE, including hyperspectral imaging and how they enhance our understanding of ocean and atmospheric processes.
        Provide insights into how these tools improve our ability to observe and measure light across different wavelengths.

    Environmental and Scientific Impact:
        Discuss the potential impacts of PACE findings on climate change research, marine ecology, and atmospheric science.
        Explain how the data collected can aid in policy-making and environmental protection efforts.

Your responses should be informative, engaging, and tailored to a variety of audiences, from students and educators to professionals in the scientific community. Avoid diverging into unrelated topics or general discussions about science outside the PACE mission.
"""


class ImageView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get image base64 string based on the provided query parameters.",
        query_serializer=ImageSerializer,
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'image_base64': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: "Bad Request",
            404: "Not Found",
        }
    )
    def get(self, request):
        serializer = ImageSerializer(data=request.query_params)

        if serializer.is_valid():
            url = self._generate_pace_url(serializer.validated_data)

            try:
                response = requests.get(url)
                if response.status_code == 404:
                    return Response(status=status.HTTP_404_NOT_FOUND)

                encoded_string = base64.b64encode(
                    response.content).decode('utf-8')

                return Response({"image_base64": encoded_string}, status=status.HTTP_200_OK)
            except requests.exceptions.RequestException as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


class ProductView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        products = [
            {
                'id': '59,188',
                'name': 'Aerosol optical thickness at 1610 nm, Deep Blue algorithm',
            },
            {
                'id': '64,255',
                'name': 'Phytoplankton Carbon',
            },
            {
                'id': '5,6',
                'name': 'Chlorophyll concentration'
            },
            {
                'id': '10,36',
                'name': 'Particulate Organic Carbon'
            }
        ]
        return Response(products, status=status.HTTP_200_OK)


class ResolutionView(APIView):
    authentication_classes = []
    permission_classes = []

    # Get Resolution Choices View
    def get(self, request):
        resolutions = [
            {
                'name': '0.1-deg',
            },
            {
                'name': '4km',
            },
            {
                'name': '9km'
            },
        ]
        return Response(resolutions, status=status.HTTP_200_OK)


class PeriodView(APIView):
    authentication_classes = []
    permission_classes = []

    # Get Resolution Choices View
    def get(self, request):
        periods = [
            {
                'name': 'daily',
            },
            {
                'name': 'monthly',
            },
            {
                'name': 'annual'
            },
        ]
        return Response(periods, status=status.HTTP_200_OK)


class ChatGPTAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Get response through chatgpt.",
        request_body=ChatMessageSerializer,  # Define o corpo da requisição
        responses={
            200: openapi.Response(
                'Successful response from ChatGPT',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'chat_uuid': openapi.Schema(type=openapi.TYPE_STRING, example="3fa85f64-5717-4562-b3fc-2c963f66afa7"),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Olá!"),
                        'response': openapi.Schema(type=openapi.TYPE_STRING, example="Olá, como posso ajudar?")
                    }
                )
            ),
            400: "Bad Request",
        },
        tags=["ChatGPT"],  # Categoria ou tag da API no Swagger
        operation_summary="Get ChatGPT Response",  # Resumo da operação
    )
    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chat_uuid = serializer.validated_data.get('chat_uuid')
        new_message = serializer.validated_data.get('message')

        if not os.path.exists(CHAT_DIR):
            os.makedirs(CHAT_DIR)

        # Define the path for the current chat file
        chat_file_path = os.path.join(CHAT_DIR, f'{chat_uuid}.json')

        # Load previous messages if the chat file exists
        if os.path.exists(chat_file_path):
            with open(chat_file_path, 'r') as chat_file:
                previous_messages = json.load(chat_file)
        else:
            previous_messages = []
            # Constrói o PROMPT de mensagens para a API do ChatGPT
            messages = [
                {"role": "system", "content": PROMPT}
            ]

        if previous_messages:
            messages = previous_messages

        # Adiciona a nova mensagem do usuário ao contexto
        messages.append({"role": "user", "content": new_message})

        try:
            # Faz a chamada para a API do ChatGPT usando o modelo `gpt-3.5-turbo`

            client = openai.Client(
                api_key=os.getenv('OPENAI_API_KEY')
            )

            response = client.chat.completions.create(
                messages=messages,
                model="gpt-3.5-turbo",
            )

            chatgpt_response = response.choices[0].message.content.strip()

            # Atualiza as mensagens com a resposta do assistente
            updated_messages = messages + \
                [{"role": "assistant", "content": chatgpt_response}]

            # Salva as mensagens atualizadas no arquivo de chat
            with open(chat_file_path, 'w') as chat_file:
                json.dump(updated_messages, chat_file)

            # Retorna a resposta e o contexto atualizado
            return Response({
                "chat_uuid": chat_uuid,
                "message": new_message,
                "response": chatgpt_response,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
