from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers import ImageURLSerializer, ChatMessageSerializer
import calendar
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import openai
import os
import json
import random
import string
# import requests

CHAT_DIR = os.path.join(os.path.dirname(__file__), 'chats')
PROMPT = "Teste"


class ImageURLView(APIView):
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get image URL based on the provided query parameters.",
        query_serializer=ImageURLSerializer,
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'url': openapi.Schema(type=openapi.TYPE_STRING, description='Generated image URL')
                }
            )),
            400: "Bad Request",
            404: "Not Found",
        }
    )
    def get(self, request):
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
                description="Success response from ChatGPT",
                examples={
                    "application/json": {
                        "chat_id": "123e4567-e89b-12d3-a456-426614174000",
                        "message": "User's message here.",
                        "response": "ChatGPT's response here."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "chat_uuid": ["chat_uuid must be a valid UUID."],
                        "message": ["message cannot be empty."]
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error",
                examples={
                    "application/json": {
                        "error": "Detailed error message here."
                    }
                }
            )
        },
        tags=["ChatGPT"],  # Categoria ou tag da API no Swagger
        operation_summary="Get ChatGPT Response",  # Resumo da operação
    )
    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chat_id = serializer.validated_data.get('chat_id')
        new_message = serializer.validated_data.get('message')

        # Define the path for the current chat file
        chat_file_path = os.path.join(CHAT_DIR, f'{chat_id}.json')

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

        # Inclui mensagens anteriores no contexto, caso fornecidas
        if previous_messages:
            messages.extend(previous_messages)

        # Adiciona a nova mensagem do usuário ao contexto
        messages.append({"role": "user", "content": new_message})

        try:
            # Faz a chamada para a API do ChatGPT usando o modelo `gpt-3.5-turbo`
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
            )

            # Extrai a resposta gerada
            chatgpt_response = response.choices[0].message['content'].strip()

            # Atualiza as mensagens com a resposta do assistente
            updated_messages = messages + \
                [{"role": "assistant", "content": chatgpt_response}]

            # Salva as mensagens atualizadas no arquivo de chat
            with open(chat_file_path, 'w') as chat_file:
                json.dump(updated_messages, chat_file)

            # Retorna a resposta e o contexto atualizado
            return Response({
                "chat_id": chat_id,
                "message": new_message,
                "response": chatgpt_response,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
