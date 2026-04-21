import logging
import asyncio
import io
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from ai_engine import get_ai_response, generate_image_url, is_image_request

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_sessions = {}

def format_text(text):
    """
    تحسين تنسيق النص ليكون مريحاً للعين في تليجرام.
    """
    # استبدال النقاط بأسطر جديدة في القوائم لزيادة الوضوح
    formatted = text.replace(". ", ".\n\n")
    return formatted

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *أهلاً بك في النسخة المطورة من البوت الذكي!* 🚀\n\n"
        "لقد تمت إضافة ميزات رهيبة:\n"
        "🖼️ *تحليل الصور:* أرسل لي أي صورة وسأشرحها لك.\n"
        "🎨 *توليد الصور:* اطلب مني رسم أي شيء (مثلاً: ارسم قطة فضاء).\n"
        "✍️ *تنسيق أفضل:* الردود الآن أكثر وضوحاً وترتيباً.\n\n"
        "اكتب /clear لمسح الذاكرة."
    )
    await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.MARKDOWN)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    await update.message.reply_text("✅ تم مسح الذاكرة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    if not user_text: return

    # 1. التحقق من طلب توليد صورة
    if is_image_request(user_text):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.UPLOAD_PHOTO)
        img_url = generate_image_url(user_text)
        await update.message.reply_photo(photo=img_url, caption=f"🎨 إليك ما تخيلته لـ: {user_text}")
        return

    # 2. التعامل مع المحادثة النصية
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    
    user_sessions[user_id].append({"role": "user", "content": user_text})
    if len(user_sessions[user_id]) > 10: user_sessions[user_id] = user_sessions[user_id][-10:]
        
    try:
        response = await get_ai_response(user_sessions[user_id])
        formatted_response = format_text(response)
        user_sessions[user_id].append({"role": "assistant", "content": response})
        await update.message.reply_text(formatted_response)
    except Exception as e:
        await update.message.reply_text("❌ عذراً، حدث خطأ في معالجة النص.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    التعامل مع الصور المرسلة من المستخدم.
    """
    user_id = update.effective_user.id
    photo_file = await update.message.photo[-1].get_file()
    
    # تحميل الصورة في الذاكرة
    photo_bytearray = await photo_file.download_as_bytearray()
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    caption = update.message.caption or "اشرح لي هذه الصورة"
    
    messages = [{"role": "user", "content": caption}]
    
    try:
        # إرسال الصورة للمحرك (تحويل bytearray إلى bytes)
        response = await get_ai_response(messages, image_data=bytes(photo_bytearray))
        await update.message.reply_text(f"🖼️ *تحليل الصورة:*\n\n{format_text(response)}", parse_mode=constants.ParseMode.MARKDOWN)
    except Exception as e:
        logging.error(f"Vision Error: {e}")
        await update.message.reply_text("❌ عذراً، لم أتمكن من تحليل هذه الصورة حالياً.")

if __name__ == '__main__':
    TOKEN = "6689597814:AAFxW347Ah9j1te3-5R6JwDhfMpeqLE6BPc"
    
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️ يرجى وضع التوكن!")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('clear', clear_history))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        print("🚀 البوت المطور يعمل الآن...")
        application.run_polling()
