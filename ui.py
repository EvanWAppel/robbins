"""Shared visual language for the Robbins city atlas."""
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent


def apply_theme():
    """Load the same design system on every page."""
    st.html(f"<style>{(ROOT / 'assets' / 'atlas.css').read_text()}</style>")


def landscape():
    """An original, decorative Pacific Northwest landscape engraving."""
    return (ROOT / 'assets' / 'landscape.svg').read_text()
