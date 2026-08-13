os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! যেকোনো মুভির .srt সাবটাইটেল ফাইল পাঠান, আমি প্রাকৃতিক ও সাবলীল বাংলায় অনুবাদ করে দেব।")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith('.srt'):
        await update.message.reply_text("অনুগ্রহ করে একটি .srt ফাইল পাঠান।")
        return

    status_msg = await update.message.reply_text("⏳ ফাইল পেয়েছি! অনুবাদের কাজ চলছে, কিছুক্ষণ অপেক্ষা করুন...")
    
    file = await context.bot.get_file(document.file_id)
    input_path = f"input_{document.file_name}"
    output_path = f"Bangla_{document.file_name}"
    await file.download_to_drive(input_path)

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            srt_content = f.read()

        prompt = f"""
        You are a professional movie subtitle translator. Translate the following SRT subtitle content into natural, fluent, conversational Bangla (বাংলা).
        
        STRICT RULES:
        1. Maintain the EXACT SRT format including index numbers and timestamps (00:00:00,000 --> 00:00:00,000).
        2. Do NOT use literal mechanical/robotic translation.
        3. Use natural dialogue and spoken Bangla appropriate for a movie.
        4. Do not alter any timestamps.

        SRT Content:
        {srt_content}
        """

        response = model.generate_content(prompt)
        translated_text = response.text

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)

        with open(output_path, 'rb') as f:
            await update.message.reply_document(document=f, caption="✅ আপনার বাংলা সাবটাইটেল তৈরি হয়ে গেছে!")

    except Exception as e:
        await update.message.reply_text(f"দুঃখিত, কোনো সমস্যা হয়েছে: {str(e)}")
    
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
                          
