import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Fetch Environment Variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Client
client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("স্বাগতম! যেকোনো ভাষার .srt সাবটাইটেল পাঠালে তা প্রাকৃতিক ও সাবলীল বাংলায় অনুবাদ হয়ে যাবে।")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith('.srt'):
        await update.message.reply_text("অনুগ্রহ করে একটি .srt ফাইল পাঠান।")
        return

    status_msg = await update.message.reply_text("⏳ ফাইল পেয়েছি! অনুবাদের কাজ চলছে, কিছুক্ষণ অপেক্ষা করুন...")

    try:
        file = await context.bot.get_file(document.file_id)
        input_filename = document.file_name
        await file.download_to_drive(input_filename)

        with open(input_filename, 'r', encoding='utf-8', errors='ignore') as f:
            srt_content = f.read()

        prompt = f"""You are an expert subtitle translator.
Translate the following SRT file into natural, conversational, and fluent Bengali (বাংলা).
Keep exact timestamps, subtitle indices, and line formatting unchanged.
Avoid literal or mechanical translation. Make it sound natural to native Bengali speakers.

SRT Content:
{srt_content}"""

        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        translated_text = response.text

        output_filename = f"translated_{input_filename}"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(translated_text)

        with open(output_filename, 'rb') as f:
            await update.message.reply_document(document=f, caption="✅ আপনার সাবলীল বাংলা অনুবাদ প্রস্তুত!")

        # Cleanup
        os.remove(input_filename)
        os.remove(output_filename)
        await status_msg.delete()

    except Exception as e:
        await update.message.reply_text(f"দুঃখিত, কোনো সমস্যা হয়েছে: {e}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == '__main__':
    main()
