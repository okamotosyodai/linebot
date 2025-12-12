from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import (
    FollowEvent, MessageEvent, TextMessageContent
)

import os
from dotenv import load_dotenv
load_dotenv()

# ---- RAG 使用部分 ----
from pdf_loader import load_pdfs
from rag_engine import load_vector_store, create_vector_store, rag_answer
# -----------------------

CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

app = Flask(__name__)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# RAG 初期化（PDF→embeddings）
def init_rag():
    vectordb = load_vector_store()
    if vectordb is None:
        print("Vector DB not found. Creating...")
        texts = load_pdfs()
        vectordb = create_vector_store(texts)
        print("Vector Store created!")
    return vectordb

VECTORDb = init_rag()  # ← サーバ起動時にロード


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(FollowEvent)
def handle_follow(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text="野々市市の生活情報をお知らせします！質問してね。")]
        )
    )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

    user_text = event.message.text

    # --- RAGで回答 ---
    answer = rag_answer(user_text, VECTORDb)

    # --- LINEへ返信 ---
    line_bot_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=answer)]
        )
    )


@app.route('/', methods=['GET'])
def toppage():
    return 'Nonoichi Life Info Bot is running.'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
