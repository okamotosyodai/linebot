# -*- coding: utf-8 -*-
# 必要なライブラリのインポート
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    # TemplateMessage, FlexMessage, etc. 必要に応じて追加
)
from linebot.v3.webhooks import (
    FollowEvent, MessageEvent, PostbackEvent, TextMessageContent
)
import os

# .env ファイル読み込み (環境変数からトークンを取得するために必要)
from dotenv import load_dotenv
load_dotenv()

# 環境変数を変数に割り当て
# CHANNEL_ACCESS_TOKENとCHANNEL_SECRETは.envファイルに記述されていることを前提とします。
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

# CHANNEL_ACCESS_TOKEN または CHANNEL_SECRET が設定されていない場合はエラーを出す
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("Error: CHANNEL_ACCESS_TOKEN or CHANNEL_SECRET is not set in environment variables.")
    # 本番環境では abort(500) などで適切にエラー処理を行うべきです。

# Flask アプリのインスタンス化
app = Flask(__name__)

# LINE API の設定
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

## --- Webhook コールバック処理 ---
@app.route("/callback", methods=['POST'])
def callback():
    # X-Line-Signature ヘッダー値を取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディをテキストとして取得
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # webhook body の処理
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

## --- イベントハンドラ ---

# 友達追加（フォロー）時のメッセージ送信
@handler.add(FollowEvent)
def handle_follow(event):
    # APIインスタンス化
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 返信メッセージ
        welcome_message = "お友達追加ありがとうございます！\n「メニュー」と入力すると、利用できる機能を確認できます。"

        line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=welcome_message)]
            )
        )

# メッセージ受信時の処理 (TextMessageContent の場合のみ)
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # APIインスタンス化
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 受信メッセージを大文字・小文字を区別しないようにトリミングして取得
        received_message = event.message.text.strip().lower()

        reply_text = ""

        # 応答ロジックの開始
        if received_message == 'メニュー':
            reply_text = (
                "【メインメニュー】\n"
                "以下のキーワードを入力してください。\n"
                "1. 自己紹介: ボットについて紹介します。\n"
                "2. 今日は何の日: 簡易的な情報を提供します。\n"
                "3. その他: オウム返し機能に戻ります。"
            )

        elif received_message == '自己紹介':
            reply_text = "私はLINE APIとPython (Flask) で作られたデモ用チャットボットです。あなたのメッセージに応じて決められた応答を返します！"

        elif received_message == '今日は何の日':
            # ここに外部APIを呼び出すなどのより複雑な処理を実装できます
            # 例: date_info = get_today_history()
            reply_text = "今日（10月31日）はハロウィンの日です！"

        elif received_message == 'その他':
            reply_text = "これ以降は、あなたが送信したメッセージをそのままオウム返しします。「メニュー」でいつでも戻れます。"

        else:
            # どのコマンドにも該当しない場合は、送信者名を含めたオウム返し
            try:
                profile = line_bot_api.get_profile(event.source.user_id)
                display_name = profile.display_name
                reply_text = (
                    f'{display_name}さん、メッセージ「{event.message.text}」を受け取りました。\n\n'
                    '（「メニュー」と入力して機能を確認してください）'
                )
            except Exception:
                # プロフィールが取得できない（グループチャットなど）場合のフォールバック
                reply_text = (
                    f'メッセージ「{event.message.text}」を受け取りました。\n\n'
                    '（「メニュー」と入力して機能を確認してください）'
                )

        # 追加してた簡易分岐（元コードの意図を残す）
        user_message = event.message.text
        if user_message == '今日は何の日':
            reply_text = '今日はゴミ出しの日です'
        # else は上のreply_textをそのまま使う

        # 返信
        line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

# 起動確認用ウェブサイトのトップページ
@app.route('/', methods=['GET'])
def toppage():
    return 'LINE Bot Server is running!'

# ボット起動コード
if __name__ == "__main__":
    # 外部からアクセスできるよう、host="0.0.0.0" を指定
    # 本番環境では、デバッグモードは必ず False にしてください。
    app.run(host="0.0.0.0", port=5000, debug=True)

