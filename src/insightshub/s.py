from nicegui import ui
from fastapi import FastAPI
app = FastAPI(title="KinD demo server")

@ui.page('/')
def index():
    ui.label('Hello from KinD!').classes('text-2xl')
    ui.label('Change this text, save, and watch it live reload!')

ui.run_with(app, title="Dev Server")

