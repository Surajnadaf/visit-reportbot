"""
Telegram Visit Report Bot
Features:
- Project details
- Multiple stakeholders
- Observations
- Action items
- Up to 8 photos
- DOCX report
- PDF report
"""

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from docx import Document
from docx.shared import Inches
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

TOKEN = "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE"

(PROJECT, LOCATION, STAKEHOLDERS, OBSERVATIONS,
 ACTIONS, PHOTOS) = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Project Name?")
    return PROJECT

async def project(update, context):
    context.user_data["project"] = update.message.text
    await update.message.reply_text("Location?")
    return LOCATION

async def location(update, context):
    context.user_data["location"] = update.message.text
    await update.message.reply_text("Stakeholders (comma separated)?")
    return STAKEHOLDERS

async def stakeholders(update, context):
    context.user_data["stakeholders"] = update.message.text
    await update.message.reply_text("Observations?")
    return OBSERVATIONS

async def observations(update, context):
    context.user_data["observations"] = update.message.text
    await update.message.reply_text("Action Items?")
    return ACTIONS

async def actions(update, context):
    context.user_data["actions"] = update.message.text
    context.user_data["photos"] = []
    await update.message.reply_text(
        "Upload up to 8 photos. Send /done when finished."
    )
    return PHOTOS

async def photo(update, context):
    photos = context.user_data["photos"]

    if len(photos) >= 8:
        await update.message.reply_text("Maximum 8 photos reached.")
        return PHOTOS

    file = await update.message.photo[-1].get_file()
    filename = f"photo_{len(photos)+1}.jpg"
    await file.download_to_drive(filename)

    photos.append(filename)

    await update.message.reply_text(
        f"Photo {len(photos)} saved."
    )
    return PHOTOS

def create_docx(data):
    doc = Document()

    doc.add_heading("Visit Report", level=1)

    table = doc.add_table(rows=0, cols=2)

    fields = [
        ("Project", data["project"]),
        ("Location", data["location"]),
        ("Stakeholders", data["stakeholders"]),
        ("Observations", data["observations"]),
        ("Action Items", data["actions"]),
    ]

    for k, v in fields:
        row = table.add_row().cells
        row[0].text = k
        row[1].text = v

    if data["photos"]:
        doc.add_page_break()
        doc.add_heading("Photographs", level=2)

        for img in data["photos"]:
            try:
                doc.add_picture(img, width=Inches(2.5))
            except:
                pass

    filename = "Visit_Report.docx"
    doc.save(filename)
    return filename

def create_pdf(data):
    filename = "Visit_Report.pdf"

    pdf = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Visit Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Project: {data['project']}", styles["BodyText"]),
        Paragraph(f"Location: {data['location']}", styles["BodyText"]),
        Paragraph(f"Stakeholders: {data['stakeholders']}", styles["BodyText"]),
        Paragraph(f"Observations: {data['observations']}", styles["BodyText"]),
        Paragraph(f"Action Items: {data['actions']}", styles["BodyText"]),
    ]

    pdf.build(elements)
    return filename

async def done(update, context):
    docx_file = create_docx(context.user_data)
    pdf_file = create_pdf(context.user_data)

    await update.message.reply_document(document=open(docx_file, "rb"))
    await update.message.reply_document(document=open(pdf_file, "rb"))

    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PROJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, project)],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            STAKEHOLDERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stakeholders)],
            OBSERVATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, observations)],
            ACTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, actions)],
            PHOTOS: [
                MessageHandler(filters.PHOTO, photo),
                CommandHandler("done", done),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
