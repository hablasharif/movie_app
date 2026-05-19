#!/usr/bin/env python3
"""
StreamVault Pro — Professional Streaming Extractor
====================================================
HiAnime / AniWatch inspired UI with trending content.

Setup:
    pip install fastapi uvicorn httpx python-dotenv

Run:
    python videasy_pro.py

Then open: http://localhost:8000
"""

import base64
import json
import os
import re
import sys
from urllib.parse import urljoin, quote, unquote, urlparse

def ensure_deps():
    import importlib
    missing = []
    for pkg, imp in [("fastapi","fastapi"),("uvicorn","uvicorn"),("httpx","httpx"),("dotenv","dotenv")]:
        try:
            importlib.import_module(imp)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[setup] Installing: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "python-dotenv"])

ensure_deps()

from dotenv import load_dotenv
load_dotenv()

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────────────────────
# HTML FRONTEND
# ──────────────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>StreamVault — Watch Anime & Movies</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/hls.js@1/dist/hls.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0a12;
  --bg2:#0f0f1a;
  --bg3:#141420;
  --card:#181825;
  --border:rgba(255,255,255,0.06);
  --border2:rgba(255,255,255,0.10);
  --purple:#7c3aed;
  --purple2:#9d5ef5;
  --purple3:#b47eff;
  --pink:#ec4899;
  --cyan:#06b6d4;
  --green:#10b981;
  --gold:#f59e0b;
  --red:#ef4444;
  --text:#f1f1f5;
  --text2:#a1a1c0;
  --text3:#52527a;
  --radius:10px;
  --radius-sm:6px;
  --nav-h:62px;
}

html{scroll-behavior:smooth}
body{
  font-family:'Outfit',sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  overflow-x:hidden;
}

/* Scrollbar */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(124,58,237,0.4);border-radius:3px}

/* ─── NAVBAR ─── */
nav{
  position:fixed;top:0;left:0;right:0;z-index:100;
  height:var(--nav-h);
  display:flex;align-items:center;
  padding:0 28px;gap:32px;
  background:rgba(10,10,18,0.85);
  backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
}
.nav-logo{
  display:flex;align-items:center;gap:10px;
  text-decoration:none;flex-shrink:0;
}
.nav-logo-mark{
  width:36px;height:36px;
  background:linear-gradient(135deg,var(--purple),var(--pink));
  border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 20px rgba(124,58,237,0.5);
}
.nav-logo-text{
  font-weight:800;font-size:18px;letter-spacing:-0.3px;
  background:linear-gradient(135deg,#fff 40%,var(--purple3));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.nav-links{
  display:flex;gap:4px;
}
.nav-link{
  background:none;border:none;cursor:pointer;
  font-family:'Outfit',sans-serif;font-size:13px;font-weight:500;
  color:var(--text2);padding:7px 14px;border-radius:var(--radius-sm);
  transition:all 0.2s;
}
.nav-link:hover{color:var(--text);background:rgba(255,255,255,0.05)}
.nav-link.active{color:var(--purple3);background:rgba(124,58,237,0.12)}
.nav-search-wrap{
  flex:1;max-width:380px;position:relative;
}
.nav-search{
  width:100%;background:rgba(255,255,255,0.04);
  border:1px solid var(--border2);
  border-radius:100px;
  color:var(--text);font-family:'Outfit',sans-serif;font-size:13px;
  padding:9px 16px 9px 40px;outline:none;
  transition:all 0.25s;
}
.nav-search::placeholder{color:var(--text3)}
.nav-search:focus{
  background:rgba(255,255,255,0.06);
  border-color:rgba(124,58,237,0.5);
  box-shadow:0 0 0 3px rgba(124,58,237,0.1);
}
.nav-search-icon{
  position:absolute;left:13px;top:50%;transform:translateY(-50%);
  color:var(--text3);pointer-events:none;
}
.nav-right{display:flex;gap:8px;align-items:center;margin-left:auto}

/* ─── PAGE SHELL ─── */
#page{padding-top:var(--nav-h)}
.page-section{display:none}
.page-section.active{display:block}

/* ─── HERO BANNER ─── */
.hero{
  position:relative;
  height:520px;overflow:hidden;
  margin-bottom:48px;
}
.hero-bg{
  position:absolute;inset:0;
  background-size:cover;background-position:center top;
  filter:blur(0px);
  transition:background-image 0.5s ease;
}
.hero-gradient{
  position:absolute;inset:0;
  background:linear-gradient(
    to right,
    rgba(10,10,18,0.98) 0%,
    rgba(10,10,18,0.85) 40%,
    rgba(10,10,18,0.3) 70%,
    transparent 100%
  ),linear-gradient(to top,rgba(10,10,18,1) 0%,transparent 40%);
}
.hero-content{
  position:relative;z-index:2;
  height:100%;
  display:flex;flex-direction:column;justify-content:flex-end;
  padding:0 60px 52px;
  max-width:620px;
}
.hero-badge{
  display:inline-flex;align-items:center;gap:6px;
  background:rgba(124,58,237,0.2);border:1px solid rgba(124,58,237,0.4);
  color:var(--purple3);border-radius:100px;
  font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;
  padding:4px 12px;margin-bottom:14px;width:fit-content;
}
.hero-title{
  font-size:42px;font-weight:900;line-height:1.1;letter-spacing:-1px;
  color:#fff;margin-bottom:12px;
  text-shadow:0 2px 20px rgba(0,0,0,0.5);
}
.hero-meta{
  display:flex;align-items:center;gap:12px;
  margin-bottom:14px;font-size:13px;color:var(--text2);flex-wrap:wrap;
}
.hero-meta-dot{width:3px;height:3px;border-radius:50%;background:var(--text3)}
.hero-rating{color:var(--gold);font-weight:700;display:flex;align-items:center;gap:4px}
.hero-desc{
  font-size:14px;color:var(--text2);line-height:1.7;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;
  margin-bottom:22px;
}
.hero-btns{display:flex;gap:10px;flex-wrap:wrap}
.btn-play{
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(135deg,var(--purple),var(--purple2));
  color:#fff;border:none;cursor:pointer;
  font-family:'Outfit',sans-serif;font-weight:700;font-size:13px;letter-spacing:0.3px;
  padding:11px 22px;border-radius:100px;
  box-shadow:0 4px 24px rgba(124,58,237,0.45);
  transition:all 0.2s;
}
.btn-play:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(124,58,237,0.6)}
.btn-info{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.12);
  color:var(--text);cursor:pointer;
  font-family:'Outfit',sans-serif;font-weight:600;font-size:13px;
  padding:11px 22px;border-radius:100px;
  transition:all 0.2s;
}
.btn-info:hover{background:rgba(255,255,255,0.13)}
.hero-dots{
  position:absolute;bottom:20px;right:60px;z-index:10;
  display:flex;gap:6px;
}
.hero-dot{
  width:6px;height:6px;border-radius:50%;
  background:var(--text3);cursor:pointer;
  transition:all 0.3s;border:none;
}
.hero-dot.active{background:var(--purple);width:24px;border-radius:3px}

/* ─── SECTION ROW ─── */
.section{padding:0 24px;margin-bottom:44px}
.section-head{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:18px;
}
.section-title-wrap{display:flex;align-items:center;gap:10px}
.section-bar{
  width:3px;height:20px;
  background:linear-gradient(to bottom,var(--purple),var(--pink));
  border-radius:2px;flex-shrink:0;
}
.section-title{font-size:17px;font-weight:800;color:var(--text);letter-spacing:-0.3px}
.section-sub{font-size:12px;color:var(--text3);margin-top:1px}
.view-all{
  font-size:12px;font-weight:600;color:var(--purple3);
  background:none;border:none;cursor:pointer;
  display:flex;align-items:center;gap:4px;
  transition:opacity 0.2s;
}
.view-all:hover{opacity:0.7}

/* ─── SCROLL ROW ─── */
.scroll-row-wrap{position:relative}
.scroll-row{
  display:flex;gap:12px;
  overflow-x:auto;padding-bottom:8px;
  scrollbar-width:none;
}
.scroll-row::-webkit-scrollbar{display:none}
.scroll-arrow{
  position:absolute;top:50%;transform:translateY(-50%);
  z-index:5;background:rgba(15,15,26,0.9);
  border:1px solid var(--border2);
  color:var(--text);border-radius:50%;
  width:36px;height:36px;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:16px;
  transition:all 0.2s;opacity:0;
  pointer-events:none;
}
.scroll-row-wrap:hover .scroll-arrow{opacity:1;pointer-events:all}
.scroll-arrow:hover{background:var(--purple);border-color:var(--purple)}
.arrow-left{left:-14px}
.arrow-right{right:-14px}

/* ─── POSTER CARD ─── */
.card{
  flex-shrink:0;width:140px;
  cursor:pointer;
  transition:transform 0.25s ease;
}
.card:hover{transform:translateY(-6px)}
.card-img{
  width:140px;height:196px;border-radius:var(--radius);overflow:hidden;
  background:var(--card);position:relative;
  border:1px solid var(--border);
}
.card-img img{
  width:100%;height:100%;object-fit:cover;
  transition:transform 0.4s ease;
  display:block;
}
.card:hover .card-img img{transform:scale(1.08)}
.card-overlay{
  position:absolute;inset:0;
  background:linear-gradient(to top,rgba(10,10,18,0.98) 0%,rgba(10,10,18,0.4) 50%,transparent 100%);
  opacity:0;transition:opacity 0.25s;
  display:flex;flex-direction:column;justify-content:flex-end;
  padding:10px;gap:6px;
}
.card:hover .card-overlay{opacity:1}
.card-play-btn{
  display:flex;align-items:center;justify-content:center;gap:6px;
  background:var(--purple);border:none;cursor:pointer;
  color:#fff;font-family:'Outfit',sans-serif;font-weight:700;font-size:10px;
  letter-spacing:0.5px;padding:7px;border-radius:6px;
  width:100%;transition:background 0.2s;
}
.card-play-btn:hover{background:var(--purple2)}
.card-score{
  position:absolute;top:7px;left:7px;
  background:rgba(0,0,0,0.75);border:1px solid rgba(245,158,11,0.3);
  color:var(--gold);font-size:10px;font-weight:700;
  padding:2px 7px;border-radius:100px;
  display:flex;align-items:center;gap:3px;
  font-family:'Space Mono',monospace;
}
.card-ep-badge{
  position:absolute;top:7px;right:7px;
  background:rgba(124,58,237,0.85);
  color:#fff;font-size:9px;font-weight:700;
  padding:2px 7px;border-radius:100px;
  font-family:'Space Mono',monospace;
  letter-spacing:0.5px;
}
.card-sub{
  position:absolute;bottom:7px;left:7px;
  background:rgba(16,185,129,0.85);
  color:#fff;font-size:9px;font-weight:700;
  padding:2px 7px;border-radius:100px;
}
.card-title{
  font-size:12px;font-weight:600;color:var(--text);
  margin-top:8px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
  overflow:hidden;line-height:1.4;
}
.card-meta-row{
  display:flex;align-items:center;gap:6px;
  font-size:10px;color:var(--text3);margin-top:3px;
  font-family:'Space Mono',monospace;
}
.card-type-dot{width:5px;height:5px;border-radius:50%}

/* ─── RANK CARD (top 20) ─── */
.rank-card{
  flex-shrink:0;width:180px;cursor:pointer;
  transition:transform 0.25s;
}
.rank-card:hover{transform:translateY(-4px)}
.rank-card-inner{
  position:relative;display:flex;gap:0;
  border-radius:var(--radius);overflow:hidden;
  border:1px solid var(--border);
  background:var(--card);height:90px;
}
.rank-num{
  font-family:'Outfit',sans-serif;font-weight:900;font-size:40px;
  color:rgba(255,255,255,0.06);line-height:1;
  position:absolute;left:8px;bottom:4px;
  letter-spacing:-3px;
  pointer-events:none;
}
.rank-img{width:64px;height:90px;object-fit:cover;flex-shrink:0}
.rank-info{
  flex:1;padding:10px;display:flex;flex-direction:column;justify-content:center;gap:4px;
  position:relative;z-index:1;
}
.rank-title{font-size:12px;font-weight:700;color:var(--text);line-height:1.3;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}
.rank-badge{
  display:inline-block;
  background:rgba(124,58,237,0.2);border:1px solid rgba(124,58,237,0.3);
  color:var(--purple3);font-size:9px;font-weight:600;
  padding:2px 6px;border-radius:4px;width:fit-content;
  font-family:'Space Mono',monospace;
}
.rank-score{color:var(--gold);font-size:10px;font-weight:700;font-family:'Space Mono',monospace;
  display:flex;align-items:center;gap:3px;}

/* ─── GRID (movies, shows) ─── */
.card-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
  gap:16px;
  padding:0 24px;
}

/* ─── MODAL / WATCH PAGE ─── */
.watch-page{
  display:none;
  position:fixed;inset:0;z-index:200;
  background:var(--bg);
  overflow-y:auto;
}
.watch-page.open{display:block}
.watch-nav{
  position:sticky;top:0;z-index:10;
  display:flex;align-items:center;gap:16px;
  padding:14px 28px;
  background:rgba(10,10,18,0.9);
  backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
}
.watch-back{
  background:rgba(255,255,255,0.05);border:1px solid var(--border2);
  color:var(--text);border-radius:var(--radius-sm);
  font-family:'Outfit',sans-serif;font-size:13px;font-weight:600;
  padding:8px 16px;cursor:pointer;
  display:flex;align-items:center;gap:6px;
  transition:all 0.2s;
}
.watch-back:hover{background:rgba(255,255,255,0.1)}
.watch-nav-title{
  font-size:14px;font-weight:700;color:var(--text);flex:1;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.watch-main{
  display:grid;
  grid-template-columns:1fr 320px;
  gap:0;
  min-height:calc(100vh - 62px);
}
.watch-left{padding:0}
.watch-right{
  background:var(--bg2);
  border-left:1px solid var(--border);
  display:flex;flex-direction:column;
}

/* Player */
.player-box{
  background:#000;
  aspect-ratio:16/9;
  position:relative;
}
.player-box video{width:100%;height:100%;display:block;background:#000}
.player-loading{
  position:absolute;inset:0;
  display:flex;align-items:center;justify-content:center;
  background:#000;
  flex-direction:column;gap:12px;
}
.spin{
  width:36px;height:36px;border:3px solid rgba(124,58,237,0.2);
  border-top-color:var(--purple);border-radius:50%;
  animation:spin 0.8s linear infinite;
}
@keyframes spin{to{transform:rotate(360deg)}}
.player-error{
  position:absolute;inset:0;
  display:none;align-items:center;justify-content:center;
  background:#000;
  color:var(--red);font-size:13px;font-family:'Space Mono',monospace;
}
.player-controls{
  background:var(--bg2);border-top:1px solid var(--border);
  padding:10px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
}
.quality-sel{
  background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.3);
  color:var(--purple3);font-family:'Space Mono',monospace;font-size:10px;
  border-radius:6px;padding:5px 8px;cursor:pointer;outline:none;
}
.quality-sel option{background:var(--bg2);color:var(--text)}
.player-label{
  font-family:'Space Mono',monospace;font-size:10px;color:var(--text3);
  display:flex;align-items:center;gap:6px;
}
.playing-dot{
  width:7px;height:7px;background:var(--purple);border-radius:50%;
  animation:blink 1.5s ease infinite;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.2}}
.stream-copy{
  background:none;border:1px solid var(--border2);color:var(--text2);
  font-family:'Space Mono',monospace;font-size:10px;
  padding:5px 10px;border-radius:6px;cursor:pointer;
  transition:all 0.2s;margin-left:auto;
}
.stream-copy:hover{border-color:var(--purple3);color:var(--purple3)}

/* Watch info */
.watch-info{padding:20px 28px}
.watch-title-row{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}
.watch-title{font-size:22px;font-weight:800;color:var(--text);letter-spacing:-0.5px;line-height:1.2}
.watch-badges{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.badge{
  font-size:10px;font-weight:700;padding:4px 10px;border-radius:100px;
  font-family:'Space Mono',monospace;letter-spacing:0.5px;
}
.badge-purple{background:rgba(124,58,237,0.2);border:1px solid rgba(124,58,237,0.35);color:var(--purple3)}
.badge-green{background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.3);color:var(--green)}
.badge-gold{background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);color:var(--gold)}
.badge-red{background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);color:var(--red)}
.watch-desc{font-size:13px;color:var(--text2);line-height:1.7}

/* Episode sidebar */
.ep-sidebar-head{
  padding:14px 16px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;
}
.ep-sidebar-title{font-size:13px;font-weight:700;color:var(--text)}
.ep-count-badge{
  background:rgba(124,58,237,0.2);color:var(--purple3);
  font-size:10px;font-weight:700;padding:2px 8px;border-radius:100px;
  font-family:'Space Mono',monospace;
}
.season-tabs{
  display:flex;gap:4px;padding:10px 12px;
  border-bottom:1px solid var(--border);
  overflow-x:auto;
  scrollbar-width:none;
}
.season-tabs::-webkit-scrollbar{display:none}
.season-tab{
  flex-shrink:0;background:transparent;
  border:1px solid var(--border2);color:var(--text2);
  font-family:'Outfit',sans-serif;font-size:11px;font-weight:600;
  padding:5px 12px;border-radius:100px;cursor:pointer;
  transition:all 0.2s;
}
.season-tab:hover{border-color:var(--purple3);color:var(--purple3)}
.season-tab.active{background:var(--purple);border-color:var(--purple);color:#fff}

/* Episode number grid */
.ep-grid{
  display:flex;flex-wrap:wrap;gap:6px;
  padding:12px;overflow-y:auto;max-height:calc(100vh - 280px);
}
.ep-num-btn{
  width:44px;height:38px;
  background:rgba(255,255,255,0.04);
  border:1px solid var(--border);
  color:var(--text2);
  font-family:'Space Mono',monospace;font-size:11px;font-weight:700;
  border-radius:var(--radius-sm);cursor:pointer;
  transition:all 0.2s;
  position:relative;
  display:flex;align-items:center;justify-content:center;
}
.ep-num-btn:hover{
  background:rgba(124,58,237,0.2);
  border-color:var(--purple);color:var(--purple3);
  z-index:1;
}
.ep-num-btn.active{
  background:var(--purple);border-color:var(--purple);color:#fff;
}
.ep-num-btn.watched{
  background:rgba(16,185,129,0.1);
  border-color:rgba(16,185,129,0.25);color:var(--green);
}
/* Tooltip */
.ep-num-btn::after{
  content:attr(data-title);
  position:absolute;
  bottom:calc(100% + 6px);left:50%;transform:translateX(-50%);
  background:var(--bg3);border:1px solid var(--border2);
  color:var(--text);font-family:'Outfit',sans-serif;
  font-size:11px;font-weight:500;
  padding:5px 9px;border-radius:6px;
  white-space:nowrap;max-width:200px;
  overflow:hidden;text-overflow:ellipsis;
  pointer-events:none;opacity:0;
  transition:opacity 0.15s;
  z-index:99;
  box-shadow:0 4px 16px rgba(0,0,0,0.4);
}
.ep-num-btn:hover::after{opacity:1}

/* Extracting state */
.extracting-overlay{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:12px;padding:60px 20px;
  font-size:13px;color:var(--text2);text-align:center;
}
.extract-error{
  margin:16px;
  background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
  border-radius:var(--radius);padding:14px;
  font-family:'Space Mono',monospace;font-size:11px;color:var(--red);
  line-height:1.7;white-space:pre-wrap;word-break:break-all;
}

/* ─── HOME TABS ─── */
.home-tabs{
  display:flex;gap:4px;padding:0 24px;margin-bottom:28px;
  overflow-x:auto;scrollbar-width:none;
}
.home-tabs::-webkit-scrollbar{display:none}
.home-tab{
  flex-shrink:0;background:transparent;
  border:1px solid var(--border2);
  color:var(--text2);font-family:'Outfit',sans-serif;font-size:12px;font-weight:600;
  padding:7px 18px;border-radius:100px;cursor:pointer;
  transition:all 0.2s;
}
.home-tab:hover{border-color:var(--purple3);color:var(--purple3)}
.home-tab.active{background:var(--purple);border-color:var(--purple);color:#fff}

/* ─── SEARCH PAGE ─── */
.search-page{padding:32px 24px}
.search-page-title{font-size:22px;font-weight:800;color:var(--text);margin-bottom:20px}
.search-type-row{display:flex;gap:6px;margin-bottom:24px}

/* ─── LOADING SKELETONS ─── */
.skel{
  background:linear-gradient(90deg,var(--card) 25%,var(--bg3) 50%,var(--card) 75%);
  background-size:300% 100%;
  animation:shim 1.5s infinite;border-radius:var(--radius);
}
@keyframes shim{0%{background-position:200% 0}100%{background-position:-100% 0}}
.skel-card{width:140px;height:196px;flex-shrink:0}

/* ─── GENERAL UTILS ─── */
.fade{animation:fadeUp 0.35s ease both}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.empty{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:80px 24px;gap:14px;color:var(--text3);text-align:center;
}
.empty svg{opacity:0.2}
.empty p{font-size:14px}

/* ─── ANIME SERVER TABS (MegaPlay / VidWish / Videasy) ─── */
.anime-srv-bar{display:flex;flex-direction:column;gap:10px;padding:12px 14px;
  margin-top:12px;background:rgba(255,255,255,0.02);
  border:1px solid var(--border);border-radius:10px}
.anime-srv-group{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.anime-srv-lbl{font-size:10px;letter-spacing:.12em;color:var(--text3);
  font-family:'Space Mono',monospace;text-transform:uppercase;
  padding:2px 8px;border:1px solid var(--border2);border-radius:99px;min-width:64px;text-align:center}
.anime-srv-btn{display:inline-flex;align-items:center;gap:6px;
  padding:6px 10px;font-size:12px;font-family:'Space Mono',monospace;
  background:rgba(255,255,255,0.04);border:1px solid var(--border);
  color:var(--text2);border-radius:8px;cursor:pointer;transition:all .15s}
.anime-srv-btn:hover{background:rgba(255,255,255,0.08);color:var(--text)}
.anime-srv-btn.active{background:var(--purple);color:#fff;border-color:var(--purple);
  box-shadow:0 0 0 1px rgba(255,255,255,0.1) inset}
.anime-srv-btn .dot{width:6px;height:6px;border-radius:50%;background:currentColor;
  opacity:.6}
.anime-srv-btn.active .dot{opacity:1;background:#fff}
#anime-iframe{display:none;width:100%;height:100%;border:0;background:#000;
  position:absolute;inset:0}
.player-box{position:relative}

/* ─── RESPONSIVE ─── */
@media(max-width:900px){
  .watch-main{grid-template-columns:1fr}
  .watch-right{border-left:none;border-top:1px solid var(--border)}
  .ep-grid{max-height:250px}
  .hero-content{padding:0 24px 40px;max-width:100%}
  .hero-title{font-size:28px}
  nav{padding:0 16px;gap:12px}
  .section{padding:0 16px}
  .hero{height:400px}
  .anime-srv-group{flex-direction:column;align-items:stretch}
  .anime-srv-lbl{align-self:flex-start}
}
</style>
</head>
<body>

<!-- ─── NAVBAR ─── -->
<nav>
  <a class="nav-logo" href="#" onclick="showHome()">
    <div class="nav-logo-mark">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
    </div>
    <span class="nav-logo-text">StreamVault</span>
  </a>
  <div class="nav-links">
    <button class="nav-link active" id="nav-home" onclick="showHome()">Home</button>
    <button class="nav-link" id="nav-anime" onclick="showSection('anime')">Anime</button>
    <button class="nav-link" id="nav-movies" onclick="showSection('movies')">Movies</button>
    <button class="nav-link" id="nav-shows" onclick="showSection('shows')">TV Shows</button>
  </div>
  <div class="nav-search-wrap">
    <svg class="nav-search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input class="nav-search" id="global-search" placeholder="Search anime, movies, shows..." oninput="onGlobalSearch(this.value)" autocomplete="off"/>
  </div>
  <div class="nav-right"></div>
</nav>

<!-- ─── PAGES ─── -->
<div id="page">

<!-- HOME -->
<div class="page-section active" id="sec-home">
  <div class="hero" id="hero">
    <div class="hero-bg" id="hero-bg"></div>
    <div class="hero-gradient"></div>
    <div class="hero-content" id="hero-content">
      <div class="hero-badge">🔥 Trending Now</div>
      <div class="hero-title" id="hero-title">Loading...</div>
      <div class="hero-meta" id="hero-meta"></div>
      <div class="hero-desc" id="hero-desc"></div>
      <div class="hero-btns">
        <button class="btn-play" id="hero-play-btn" onclick="heroPlay()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Watch Now
        </button>
        <button class="btn-info" id="hero-info-btn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          More Info
        </button>
      </div>
    </div>
    <div class="hero-dots" id="hero-dots"></div>
  </div>

  <div class="home-tabs">
    <button class="home-tab active" onclick="filterHome('all',this)">All</button>
    <button class="home-tab" onclick="filterHome('anime',this)">Anime</button>
    <button class="home-tab" onclick="filterHome('movie',this)">Movies</button>
    <button class="home-tab" onclick="filterHome('tv',this)">TV Shows</button>
  </div>

  <div id="home-sections"></div>
</div>

<!-- ANIME -->
<div class="page-section" id="sec-anime">
  <div style="height:40px"></div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap">
        <div class="section-bar"></div>
        <div>
          <div class="section-title">Top 20 Anime All Time</div>
          <div class="section-sub">Most loved by fans worldwide</div>
        </div>
      </div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="anime-top20"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap">
        <div class="section-bar"></div>
        <div><div class="section-title">Trending This Season</div></div>
      </div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="anime-trending"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap">
        <div class="section-bar"></div>
        <div><div class="section-title">Popular Movies</div></div>
      </div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="anime-movies"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
</div>

<!-- MOVIES -->
<div class="page-section" id="sec-movies">
  <div style="height:40px"></div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap"><div class="section-bar"></div><div><div class="section-title">Trending Movies</div></div></div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="movies-trending"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap"><div class="section-bar"></div><div><div class="section-title">Top Rated of All Time</div></div></div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="movies-toprated"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap"><div class="section-bar"></div><div><div class="section-title">Now Playing</div></div></div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="movies-nowplaying"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
</div>

<!-- TV SHOWS -->
<div class="page-section" id="sec-shows">
  <div style="height:40px"></div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap"><div class="section-bar"></div><div><div class="section-title">Trending TV Shows</div></div></div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="shows-trending"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
  <div class="section">
    <div class="section-head">
      <div class="section-title-wrap"><div class="section-bar"></div><div><div class="section-title">Top Rated Series</div></div></div>
    </div>
    <div class="scroll-row-wrap">
      <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
      <div class="scroll-row" id="shows-toprated"></div>
      <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
    </div>
  </div>
</div>

<!-- SEARCH -->
<div class="page-section" id="sec-search">
  <div class="search-page">
    <div class="search-page-title" id="search-page-title">Search Results</div>
    <div class="search-type-row">
      <button class="home-tab active" id="stype-movie" onclick="setSType('movie',this)">Movies</button>
      <button class="home-tab" id="stype-tv" onclick="setSType('tv',this)">TV Shows</button>
      <button class="home-tab" id="stype-anime" onclick="setSType('anime',this)">Anime</button>
    </div>
    <div class="card-grid" id="search-results-grid"></div>
  </div>
</div>

</div><!-- /page -->

<!-- ─── WATCH PAGE (overlay) ─── -->
<div class="watch-page" id="watch-page">
  <div class="watch-nav">
    <button class="watch-back" onclick="closeWatch()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5"/><path d="m12 5-7 7 7 7"/></svg>
      Back
    </button>
    <div class="watch-nav-title" id="watch-nav-title"></div>
  </div>
  <div class="watch-main">
    <div class="watch-left">
      <div class="player-box">
        <div class="player-loading" id="player-loading">
          <div class="spin"></div>
          <div style="font-size:12px;color:var(--text2);font-family:'Space Mono',monospace">Extracting stream…</div>
        </div>
        <div class="player-error" id="player-err"></div>
        <video id="hls-video" controls style="display:none"></video>
        <iframe id="anime-iframe" allowfullscreen
          sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-presentation"
          referrerpolicy="no-referrer"></iframe>
      </div>
      <div class="anime-srv-bar" id="anime-srv-bar" style="display:none"></div>
      <div class="player-controls" id="player-controls" style="display:none">
        <div class="player-label">
          <span class="playing-dot"></span>
          NOW PLAYING
        </div>
        <div id="quality-bar"></div>
        <button class="stream-copy" id="copy-btn" onclick="copyStream()">⎘ Copy URL</button>
      </div>
      <div id="extract-err-box"></div>
      <div class="watch-info" id="watch-info"></div>
    </div>
    <div class="watch-right" id="watch-right">
      <div class="ep-sidebar-head">
        <span class="ep-sidebar-title" id="ep-sidebar-label">Episodes</span>
        <span class="ep-count-badge" id="ep-count-badge"></span>
      </div>
      <div class="season-tabs" id="season-tabs"></div>
      <div class="ep-grid" id="ep-grid"></div>
    </div>
  </div>
</div>

<script>
// ─────────────────────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────────────────────
const S = {
  heroItems: [],
  heroIdx: 0,
  heroTimer: null,
  homeFilter: 'all',
  searchQuery: '',
  searchType: 'movie',
  searchTimer: null,
  // Watch
  watchItem: null,
  watchType: '',       // movie | tv | anime
  watchSeason: 1,
  watchEp: null,
  seasons: [],
  episodes: [],
  activeStream: null,
  hlsInstance: null,
  extracting: false,
  // Anime
  animeMalId: null,    // MyAnimeList ID (from AniList idMal or Jikan)
  animeAlId:  null,    // AniList ID
  animeSrvId: 'mp-mal-sub',   // currently selected anime server
};

// ─── ANIME PLAYER PROVIDERS ─────────────────────────────────────────
// MegaPlay & VidWish use the MAL id; AniList variants use the AniList id.
// Videasy is the original built-in HLS extractor (inline <video>).
const ANIME_MAL_SERVERS = [
  { id:'mp-mal-sub', label:'MegaPlay SUB', icon:'🎌',
    buildUrl:(malId,ep)=>`https://megaplay.buzz/stream/mal/${malId}/${ep}/sub` },
  { id:'mp-mal-dub', label:'MegaPlay DUB', icon:'🇺🇸',
    buildUrl:(malId,ep)=>`https://megaplay.buzz/stream/mal/${malId}/${ep}/dub` },
  { id:'vw-mal-sub', label:'VidWish SUB',  icon:'📺',
    buildUrl:(malId,ep)=>`https://vidwish.live/stream/mal/${malId}/${ep}/sub` },
  { id:'vw-mal-dub', label:'VidWish DUB',  icon:'🔊',
    buildUrl:(malId,ep)=>`https://vidwish.live/stream/mal/${malId}/${ep}/dub` },
];
const ANIME_AL_SERVERS = [
  { id:'mp-al-sub', label:'AniList SUB', icon:'🎌',
    buildUrl:(alId,ep)=>`https://megaplay.buzz/stream/ani/${alId}/${ep}/sub` },
  { id:'mp-al-dub', label:'AniList DUB', icon:'🇺🇸',
    buildUrl:(alId,ep)=>`https://megaplay.buzz/stream/ani/${alId}/${ep}/dub` },
];
const ANIME_HLS_SERVER = { id:'videasy-hls', label:'Videasy HLS', icon:'🎬' };
const DEFAULT_ANIME_SRV = 'mp-mal-sub';

// ─────────────────────────────────────────────────────────────────────────────
// NAV
// ─────────────────────────────────────────────────────────────────────────────
function showHome() {
  showSectionById('home');
  setActiveNav('nav-home');
}
function showSection(name) {
  showSectionById(name);
  const navMap={anime:'nav-anime',movies:'nav-movies',shows:'nav-shows'};
  setActiveNav(navMap[name]||'nav-home');
}
function showSectionById(id) {
  document.querySelectorAll('.page-section').forEach(el=>el.classList.remove('active'));
  document.getElementById('sec-'+id).classList.add('active');
}
function setActiveNav(id) {
  document.querySelectorAll('.nav-link').forEach(el=>el.classList.remove('active'));
  const el=document.getElementById(id);
  if(el) el.classList.add('active');
}

// ─────────────────────────────────────────────────────────────────────────────
// SCROLL ROW
// ─────────────────────────────────────────────────────────────────────────────
function scrollRow(btn, dir) {
  const wrap = btn.closest('.scroll-row-wrap');
  const row = wrap.querySelector('.scroll-row');
  row.scrollBy({ left: dir * 480, behavior: 'smooth' });
}

// ─────────────────────────────────────────────────────────────────────────────
// HERO
// ─────────────────────────────────────────────────────────────────────────────
function setHero(items) {
  S.heroItems = items;
  S.heroIdx = 0;
  renderHero();
  renderHeroDots();
  clearInterval(S.heroTimer);
  S.heroTimer = setInterval(() => {
    S.heroIdx = (S.heroIdx + 1) % S.heroItems.length;
    renderHero();
    renderHeroDots();
  }, 6000);
}
function renderHero() {
  const item = S.heroItems[S.heroIdx];
  if (!item) return;
  const bg = document.getElementById('hero-bg');
  bg.style.backgroundImage = item.backdrop
    ? `url(https://image.tmdb.org/t/p/original${item.backdrop})`
    : '';
  document.getElementById('hero-title').textContent = item.title;
  document.getElementById('hero-desc').textContent = item.overview || '';
  const meta = document.getElementById('hero-meta');
  const parts = [];
  if (item.rating) parts.push(`<span class="hero-rating">★ ${item.rating}</span>`);
  if (item.year) parts.push(`<span>${item.year}</span>`);
  if (item.genre) parts.push(`<span>${item.genre}</span>`);
  if (item.type) parts.push(`<span style="color:var(--purple3);font-weight:600">${item.type.toUpperCase()}</span>`);
  meta.innerHTML = parts.join('<span class="hero-meta-dot"></span>');
  document.getElementById('hero-play-btn').dataset.item = JSON.stringify(item);
  document.getElementById('hero-info-btn').onclick = () => openWatch(item);
}
function renderHeroDots() {
  const el = document.getElementById('hero-dots');
  el.innerHTML = S.heroItems.map((_, i) =>
    `<button class="hero-dot${i===S.heroIdx?' active':''}" onclick="setHeroIdx(${i})"></button>`
  ).join('');
}
function setHeroIdx(i) {
  S.heroIdx = i;
  clearInterval(S.heroTimer);
  S.heroTimer = setInterval(()=>{S.heroIdx=(S.heroIdx+1)%S.heroItems.length;renderHero();renderHeroDots();},6000);
  renderHero(); renderHeroDots();
}
function heroPlay() {
  const btn = document.getElementById('hero-play-btn');
  const item = JSON.parse(btn.dataset.item||'null');
  if (item) openWatch(item);
}

// ─────────────────────────────────────────────────────────────────────────────
// CARD HTML
// ─────────────────────────────────────────────────────────────────────────────
function cardHtml(item) {
  const img = item.posterPath
    ? `<img src="${item.posterPath}" alt="${esc(item.title)}" loading="lazy"/>`
    : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:12px;font-size:11px;color:var(--text3);text-align:center;font-weight:600">${esc(item.title)}</div>`;
  const score = item.rating ? `<div class="card-score">★ ${item.rating}</div>` : '';
  const epBadge = item.episodeCount ? `<div class="card-ep-badge">${item.episodeCount} EP</div>` : '';
  const subBadge = item.type==='anime' ? `<div class="card-sub">SUB</div>` : '';
  const typeColor = item.type==='anime'?'var(--purple)':item.type==='movie'?'var(--cyan)':'var(--pink)';
  const typeLabel = item.type==='anime'?'ANIME':item.type==='movie'?'MOVIE':'TV';
  return `<div class="card fade" onclick='openWatch(${JSON.stringify(item)})'>
    <div class="card-img">
      ${img}
      ${score}${epBadge}${subBadge}
      <div class="card-overlay">
        <button class="card-play-btn">▶ Watch Now</button>
      </div>
    </div>
    <div class="card-title">${esc(item.title)}</div>
    <div class="card-meta-row">
      <div class="card-type-dot" style="background:${typeColor}"></div>
      <span>${typeLabel}</span>
      ${item.year?`<span>·</span><span>${item.year}</span>`:''}
    </div>
  </div>`;
}

function rankCardHtml(item, rank) {
  const img = item.posterPath
    ? `<img class="rank-img" src="${item.posterPath}" alt="${esc(item.title)}" loading="lazy"/>`
    : `<div class="rank-img" style="display:flex;align-items:center;justify-content:center;font-size:10px;color:var(--text3);background:var(--bg3);">${esc(item.title[0])}</div>`;
  return `<div class="rank-card" onclick='openWatch(${JSON.stringify(item)})'>
    <div class="rank-card-inner">
      <div class="rank-num">${rank}</div>
      ${img}
      <div class="rank-info">
        <div class="rank-title">${esc(item.title)}</div>
        ${item.rating?`<div class="rank-score">★ ${item.rating}</div>`:''}
        ${item.year?`<div class="rank-badge">${item.year}</div>`:''}
      </div>
    </div>
  </div>`;
}

function skels(n=8) {
  return Array.from({length:n}).map(()=>`<div class="skel skel-card"></div>`).join('');
}

function fillRow(id, items, useRank=false) {
  const el = document.getElementById(id);
  if (!el) return;
  if (!items.length) { el.innerHTML = `<div class="empty" style="padding:40px 24px"><p>No content found</p></div>`; return; }
  el.innerHTML = useRank
    ? items.map((x,i)=>rankCardHtml(x,i+1)).join('')
    : items.map(x=>cardHtml(x)).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// HOME SECTIONS
// ─────────────────────────────────────────────────────────────────────────────
function filterHome(f, btn) {
  S.homeFilter = f;
  document.querySelectorAll('.home-tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderHomeSections();
}

const homeRowDefs = [
  { id:'home-anime-top', title:'Top Anime All Time', sub:'Highest rated ever', key:'anime-top', type:'anime', rank:true },
  { id:'home-anime-trend', title:'Trending Anime', sub:'Popular this season', key:'anime-trend', type:'anime' },
  { id:'home-movie-trend', title:'Trending Movies', sub:'Hot right now', key:'movie-trend', type:'movie' },
  { id:'home-movie-top', title:'Top Rated Movies', sub:'All time classics', key:'movie-top', type:'movie' },
  { id:'home-show-trend', title:'Trending TV Shows', sub:'Binge-worthy now', key:'show-trend', type:'tv' },
];

function renderHomeSections() {
  const container = document.getElementById('home-sections');
  const visible = homeRowDefs.filter(d =>
    S.homeFilter==='all' ||
    (S.homeFilter==='anime' && d.type==='anime') ||
    (S.homeFilter==='movie' && d.type==='movie') ||
    (S.homeFilter==='tv' && d.type==='tv')
  );
  container.innerHTML = visible.map(d => `
    <div class="section">
      <div class="section-head">
        <div class="section-title-wrap">
          <div class="section-bar"></div>
          <div>
            <div class="section-title">${d.title}</div>
            <div class="section-sub">${d.sub}</div>
          </div>
        </div>
      </div>
      <div class="scroll-row-wrap">
        <button class="scroll-arrow arrow-left" onclick="scrollRow(this,-1)">‹</button>
        <div class="scroll-row" id="${d.id}">${skels(8)}</div>
        <button class="scroll-arrow arrow-right" onclick="scrollRow(this,1)">›</button>
      </div>
    </div>`).join('');
  visible.forEach(d => {
    if (dataCache[d.key]) fillRow(d.id, dataCache[d.key], d.rank);
    else loadAndFill(d);
  });
}

const dataCache = {};

async function loadAndFill(def) {
  const data = await fetchContent(def.key);
  dataCache[def.key] = data;
  fillRow(def.id, data, def.rank);
}

async function fetchContent(key) {
  const endpoints = {
    'anime-top':    '/api/content/anime/top',
    'anime-trend':  '/api/content/anime/trending',
    'anime-movie':  '/api/content/anime/movies',
    'movie-trend':  '/api/content/movies/trending',
    'movie-top':    '/api/content/movies/toprated',
    'movie-now':    '/api/content/movies/nowplaying',
    'show-trend':   '/api/content/shows/trending',
    'show-top':     '/api/content/shows/toprated',
  };
  try {
    const res = await fetch(endpoints[key]||'/api/content/movies/trending');
    return res.ok ? await res.json() : [];
  } catch { return []; }
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION PAGES LOAD
// ─────────────────────────────────────────────────────────────────────────────
async function loadAnimePage() {
  const keys = ['anime-top','anime-trend','anime-movie'];
  const ids  = ['anime-top20','anime-trending','anime-movies'];
  const rank = [true, false, false];
  ids.forEach(id=>{ const el=document.getElementById(id); if(el) el.innerHTML=skels(8); });
  for (let i=0;i<keys.length;i++) {
    const data = dataCache[keys[i]] || await fetchContent(keys[i]);
    dataCache[keys[i]] = data;
    fillRow(ids[i], data, rank[i]);
  }
}
async function loadMoviesPage() {
  const keys = ['movie-trend','movie-top','movie-now'];
  const ids  = ['movies-trending','movies-toprated','movies-nowplaying'];
  ids.forEach(id=>{ const el=document.getElementById(id); if(el) el.innerHTML=skels(8); });
  for (let i=0;i<keys.length;i++) {
    const data = dataCache[keys[i]] || await fetchContent(keys[i]);
    dataCache[keys[i]] = data;
    fillRow(ids[i], data, false);
  }
}
async function loadShowsPage() {
  const keys = ['show-trend','show-top'];
  const ids  = ['shows-trending','shows-toprated'];
  ids.forEach(id=>{ const el=document.getElementById(id); if(el) el.innerHTML=skels(8); });
  for (let i=0;i<keys.length;i++) {
    const data = dataCache[keys[i]] || await fetchContent(keys[i]);
    dataCache[keys[i]] = data;
    fillRow(ids[i], data, false);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SEARCH
// ─────────────────────────────────────────────────────────────────────────────
function onGlobalSearch(val) {
  S.searchQuery = val.trim();
  clearTimeout(S.searchTimer);
  if (!S.searchQuery) return;
  S.searchTimer = setTimeout(runSearch, 360);
  showSectionById('search');
  setActiveNav('');
  document.getElementById('search-page-title').textContent = `Results for "${S.searchQuery}"`;
}

function setSType(t, btn) {
  S.searchType = t;
  document.querySelectorAll('#sec-search .home-tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  if (S.searchQuery) runSearch();
}

async function runSearch() {
  const grid = document.getElementById('search-results-grid');
  grid.innerHTML = skels(12).replace(/skel-card/g,'skel skel-card').replace(/class="skel skel-card skel skel-card/g,'class="skel skel-card');
  grid.innerHTML = `<div class="skel" style="height:196px;"></div>`.repeat(12);
  try {
    const res = await fetch(`/api/media/search?q=${encodeURIComponent(S.searchQuery)}&type=${S.searchType}`);
    const items = res.ok ? await res.json() : [];
    if (!items.length) {
      grid.innerHTML = `<div class="empty" style="grid-column:1/-1"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><p>No results found for "${esc(S.searchQuery)}"</p></div>`;
    } else {
      grid.innerHTML = items.map(x=>cardHtml(x)).join('');
    }
  } catch {
    grid.innerHTML = `<div class="empty" style="grid-column:1/-1"><p>Search failed. Try again.</p></div>`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// WATCH PAGE
// ─────────────────────────────────────────────────────────────────────────────
async function openWatch(item) {
  S.watchItem = item;
  S.watchType = item.type;
  S.watchSeason = 1;
  S.watchEp = null;
  S.seasons = [];
  S.episodes = [];
  S.activeStream = null;

  const wp = document.getElementById('watch-page');
  wp.classList.add('open');
  document.body.style.overflow = 'hidden';

  document.getElementById('watch-nav-title').textContent = item.title;
  renderWatchInfo(item);
  resetPlayer();

  const right = document.getElementById('watch-right');

  // Anime-only UI elements are hidden by default; setupAnimeSidebar enables them.
  const animeBar = document.getElementById('anime-srv-bar');
  if (animeBar) { animeBar.style.display = 'none'; animeBar.innerHTML = ''; }
  const animeIframe = document.getElementById('anime-iframe');
  if (animeIframe) { animeIframe.src = ''; animeIframe.style.display = 'none'; }

  if (item.type === 'movie') {
    // No sidebar needed — hide episode panel, auto-extract
    right.style.display = 'none';
    extractAndPlay(`https://player.videasy.net/movie/${item.id}`);
  } else if (item.type === 'anime') {
    right.style.display = 'flex';
    setupAnimeSidebar(item);
  } else if (item.type === 'tv') {
    right.style.display = 'flex';
    setupTvSidebar(item);
  }
}

function closeWatch() {
  const wp = document.getElementById('watch-page');
  wp.classList.remove('open');
  document.body.style.overflow = '';
  if (S.hlsInstance) { S.hlsInstance.destroy(); S.hlsInstance = null; }
  const video = document.getElementById('hls-video');
  video.pause();
  video.src = '';
  video.style.display = 'none';
  const iframe = document.getElementById('anime-iframe');
  if (iframe) { iframe.src = ''; iframe.style.display = 'none'; }
  const bar = document.getElementById('anime-srv-bar');
  if (bar) { bar.style.display = 'none'; bar.innerHTML = ''; }
  document.getElementById('player-loading').style.display = 'flex';
  document.getElementById('player-controls').style.display = 'none';
  document.getElementById('extract-err-box').innerHTML = '';
}

function resetPlayer() {
  if (S.hlsInstance) { S.hlsInstance.destroy(); S.hlsInstance = null; }
  const video = document.getElementById('hls-video');
  video.pause(); video.src = ''; video.style.display = 'none';
  const iframe = document.getElementById('anime-iframe');
  if (iframe) { iframe.src = ''; iframe.style.display = 'none'; }
  document.getElementById('player-loading').style.display = 'flex';
  document.getElementById('player-err').style.display = 'none';
  document.getElementById('player-controls').style.display = 'none';
  document.getElementById('extract-err-box').innerHTML = '';
  document.getElementById('quality-bar').innerHTML = '';
}

function renderWatchInfo(item) {
  const el = document.getElementById('watch-info');
  const badges = [
    item.type ? `<span class="badge badge-purple">${item.type.toUpperCase()}</span>` : '',
    item.rating ? `<span class="badge badge-gold">★ ${item.rating}</span>` : '',
    item.year ? `<span class="badge badge-green">${item.year}</span>` : '',
    item.episodeCount ? `<span class="badge badge-red">${item.episodeCount} EP</span>` : '',
  ].filter(Boolean).join('');
  el.innerHTML = `
    <div class="watch-title-row">
      <div class="watch-title">${esc(item.title)}</div>
    </div>
    <div class="watch-badges">${badges}</div>
    <div class="watch-desc">${esc(item.overview||'No description available.')}</div>`;
}

// ─── ANIME SIDEBAR ─────────────────────────────────────────────────────────
async function setupAnimeSidebar(item) {
  // AniList id is the catalogue id used by /api/content/anime/*
  S.animeAlId  = item.id;
  S.animeMalId = item.malId || null;
  S.animeSrvId = DEFAULT_ANIME_SRV;

  let epCount = item.episodeCount || 0;

  // Resolve MAL id (via Jikan) if AniList didn't provide it,
  // or refine the episode count if AniList didn't have it.
  if (!S.animeMalId || !epCount) {
    try {
      const r = await fetch(`/api/anime/resolve?anilist_id=${item.id}` +
        (item.title ? `&title=${encodeURIComponent(item.title)}` : ''));
      if (r.ok) {
        const j = await r.json();
        if (j.malId && !S.animeMalId) S.animeMalId = j.malId;
        if (j.episodes && !epCount) epCount = j.episodes;
      }
    } catch {}
  }
  // Fall back to AniList-based MegaPlay if MAL still unknown
  if (!S.animeMalId) S.animeSrvId = 'mp-al-sub';

  document.getElementById('ep-sidebar-label').textContent = 'Episodes';
  document.getElementById('ep-count-badge').textContent = epCount ? `${epCount} EP` : '';
  document.getElementById('season-tabs').innerHTML = '';

  // Render the MegaPlay / VidWish / AniList / Videasy server tabs
  buildAnimeServerBar();

  const grid = document.getElementById('ep-grid');
  if (!epCount) {
    grid.innerHTML = `<div style="padding:20px;font-size:12px;color:var(--text3);width:100%">Episode count unknown.<br>Enter manually:</div>
      <div style="padding:0 12px;width:100%">
        <input id="anime-ep-manual" type="number" min="1" placeholder="Episode #"
          style="width:100%;background:rgba(255,255,255,0.05);border:1px solid var(--border2);border-radius:6px;color:var(--text);font-family:'Space Mono',monospace;font-size:13px;padding:8px;outline:none;margin-bottom:8px"
        />
        <button onclick="playAnimeEp(document.getElementById('anime-ep-manual').value)" class="btn-play" style="width:100%;justify-content:center;border-radius:8px;padding:9px">▶ Watch</button>
      </div>`;
    return;
  }
  let html = '';
  for (let i=1;i<=epCount;i++) {
    html += `<button class="ep-num-btn" id="aep-${i}" data-title="Episode ${i}" onclick="playAnimeEp(${i})">${i}</button>`;
  }
  grid.innerHTML = html;

  // Auto-play episode 1 on the default (MegaPlay) server
  playAnimeEp(1);
}

// ─── ANIME SERVER BAR ────────────────────────────────────────────
function buildAnimeServerBar() {
  const bar = document.getElementById('anime-srv-bar');
  bar.innerHTML = '';
  bar.style.display = 'flex';

  // MAL group — uses Jikan/AniList MAL id, drives MegaPlay & VidWish
  if (S.animeMalId) {
    const g = document.createElement('div');
    g.className = 'anime-srv-group';
    g.innerHTML = `<span class="anime-srv-lbl">MAL ${S.animeMalId}</span>`;
    ANIME_MAL_SERVERS.forEach(s => g.appendChild(makeAnimeSrvBtn(s)));
    bar.appendChild(g);
  }

  // AniList group — fallback when MAL id is missing
  if (S.animeAlId) {
    const g = document.createElement('div');
    g.className = 'anime-srv-group';
    g.innerHTML = `<span class="anime-srv-lbl">AL ${S.animeAlId}</span>`;
    ANIME_AL_SERVERS.forEach(s => g.appendChild(makeAnimeSrvBtn(s)));
    bar.appendChild(g);
  }

  // Direct HLS group — original Videasy extractor
  const g3 = document.createElement('div');
  g3.className = 'anime-srv-group';
  g3.innerHTML = `<span class="anime-srv-lbl">DIRECT</span>`;
  g3.appendChild(makeAnimeSrvBtn(ANIME_HLS_SERVER));
  bar.appendChild(g3);
}

function makeAnimeSrvBtn(s) {
  const btn = document.createElement('button');
  btn.className = 'anime-srv-btn' + (s.id === S.animeSrvId ? ' active' : '');
  btn.dataset.srvid = s.id;
  btn.innerHTML = `<span class="dot"></span>${s.icon} ${s.label}`;
  btn.onclick = () => {
    document.querySelectorAll('.anime-srv-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    S.animeSrvId = s.id;
    if (S.watchEp) playAnimeEp(S.watchEp);
  };
  return btn;
}

// ─── ANIME EPISODE PLAYBACK ──────────────────────────────────────
function playAnimeEp(ep) {
  if (!ep) return;
  S.watchEp = ep;
  document.querySelectorAll('.ep-num-btn').forEach(b => {
    b.classList.toggle('active', parseInt(b.textContent) === parseInt(ep));
  });
  resetPlayer();

  const mp = ANIME_MAL_SERVERS.find(x => x.id === S.animeSrvId);
  const al = ANIME_AL_SERVERS.find(x => x.id === S.animeSrvId);

  if (mp && S.animeMalId) {
    // MegaPlay / VidWish — uses the MAL id automatically
    playAnimeIframe(mp.buildUrl(S.animeMalId, ep));
  } else if (al && S.animeAlId) {
    // MegaPlay AniList variant
    playAnimeIframe(al.buildUrl(S.animeAlId, ep));
  } else {
    // Videasy HLS extractor — falls through to inline <video>
    hideAnimeIframe();
    extractAndPlay(`https://player.videasy.net/anime/${S.animeAlId || S.watchItem.id}/${ep}`);
  }
}

function playAnimeIframe(url) {
  const video  = document.getElementById('hls-video');
  const iframe = document.getElementById('anime-iframe');
  const loader = document.getElementById('player-loading');
  const ctrls  = document.getElementById('player-controls');
  const errBox = document.getElementById('extract-err-box');

  if (S.hlsInstance) { try { S.hlsInstance.destroy(); } catch {} S.hlsInstance = null; }
  video.pause(); video.src = ''; video.style.display = 'none';
  loader.style.display = 'none';
  ctrls.style.display  = 'none';
  errBox.innerHTML     = '';

  iframe.src           = url;
  iframe.style.display = 'block';
}

function hideAnimeIframe() {
  const iframe = document.getElementById('anime-iframe');
  iframe.src = '';
  iframe.style.display = 'none';
}

// ─── TV SIDEBAR ─────────────────────────────────────────────────────────────
async function setupTvSidebar(item) {
  document.getElementById('ep-sidebar-label').textContent = 'Episodes';
  document.getElementById('ep-count-badge').textContent = '';
  document.getElementById('season-tabs').innerHTML = '<div style="font-size:11px;color:var(--text3);padding:4px">Loading seasons…</div>';
  document.getElementById('ep-grid').innerHTML = '';

  try {
    const res = await fetch(`/api/media/tv/${item.id}/seasons`);
    S.seasons = res.ok ? await res.json() : [];
  } catch { S.seasons = []; }

  if (!S.seasons.length) {
    document.getElementById('season-tabs').innerHTML = '<div style="font-size:11px;color:var(--text3);padding:4px">No seasons found.</div>';
    return;
  }
  renderSeasonTabs();
  selectSeason(S.seasons[0]);
}

function renderSeasonTabs() {
  const el = document.getElementById('season-tabs');
  el.innerHTML = S.seasons.map(s =>
    `<button class="season-tab${s.number===S.watchSeason?' active':''}" onclick="selectSeason(${JSON.stringify(s).replace(/"/g,'&quot;')})">${esc(s.name)}</button>`
  ).join('');
}

async function selectSeason(s) {
  S.watchSeason = s.number;
  renderSeasonTabs();
  document.getElementById('ep-count-badge').textContent = `${s.episodeCount||'?'} EP`;
  document.getElementById('ep-grid').innerHTML = `<div class="extracting-overlay"><div class="spin"></div><span>Loading episodes…</span></div>`;

  try {
    const res = await fetch(`/api/media/tv/${S.watchItem.id}/seasons/${s.number}/episodes`);
    S.episodes = res.ok ? await res.json() : [];
  } catch { S.episodes = []; }

  renderEpGrid();
}

function renderEpGrid() {
  const grid = document.getElementById('ep-grid');
  if (!S.episodes.length) {
    grid.innerHTML = `<div style="padding:20px;font-size:12px;color:var(--text3)">No episodes found.</div>`;
    return;
  }
  grid.innerHTML = S.episodes.map(e => {
    const title = e.name || `Episode ${e.number}`;
    return `<button class="ep-num-btn${S.watchEp===e.number?' active':''}"
      id="tep-${e.number}"
      data-title="${esc(title)}"
      onclick="playTvEp(${e.number})">
      ${e.number}
    </button>`;
  }).join('');
}

function playTvEp(epNum) {
  S.watchEp = epNum;
  document.querySelectorAll('#ep-grid .ep-num-btn').forEach(b=>{
    b.classList.toggle('active', parseInt(b.textContent.trim())===epNum);
  });
  resetPlayer();
  extractAndPlay(`https://player.videasy.net/tv/${S.watchItem.id}/${S.watchSeason}/${epNum}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// EXTRACT & PLAY (USING THE PROXY: https://foxy-doxy.andruilsyestems.workers.dev/)
// ─────────────────────────────────────────────────────────────────────────────
async function extractAndPlay(url) {
  S.extracting = true;
  S.activeStream = null;
  document.getElementById('extract-err-box').innerHTML = '';
  document.getElementById('player-loading').style.display = 'flex';
  document.getElementById('player-controls').style.display = 'none';
  const video = document.getElementById('hls-video');
  video.style.display = 'none';

  try {
    const res = await fetch('/api/streams/extract', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({url})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail?.error || data.error || 'Extraction failed');
    if (!data.streams || !data.streams.length) throw new Error('No streams found');
    S.activeStream = data.streams[0];
    // Use the custom proxy for fetching the stream
    const proxyUrl = `https://foxy-doxy.andruilsyestems.workers.dev/?url=${encodeURIComponent(S.activeStream)}`;
    mountPlayer(proxyUrl);
  } catch(e) {
    document.getElementById('player-loading').style.display = 'none';
    document.getElementById('extract-err-box').innerHTML = `
      <div class="extract-error">✕ ${esc(e.message)}</div>`;
  }
  S.extracting = false;
}

const QUALITY_LS = 'sv_qual';
function getPrefH() { try{return parseInt(localStorage.getItem(QUALITY_LS)||'720',10)}catch{return 720} }
function savePrefH(h) { try{localStorage.setItem(QUALITY_LS,String(h))}catch{} }

let playerLevels = [];

function mountPlayer(src) {
  const video = document.getElementById('hls-video');
  if (S.hlsInstance) { S.hlsInstance.destroy(); S.hlsInstance = null; }
  playerLevels = [];

  // Make sure the MegaPlay iframe is hidden when HLS playback starts
  const animeIframe = document.getElementById('anime-iframe');
  if (animeIframe) { animeIframe.src = ''; animeIframe.style.display = 'none'; }

  document.getElementById('player-loading').style.display = 'none';
  document.getElementById('player-err').style.display = 'none';
  video.style.display = 'block';
  document.getElementById('player-controls').style.display = 'flex';

  if (Hls.isSupported()) {
    const hls = new Hls({ startLevel:-1 });
    S.hlsInstance = hls;
    hls.loadSource(src);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
      const parsed = data.levels.map((l,i)=>({index:i,height:l.height||0,label:l.height?`${l.height}p`:`Track ${i+1}`}));
      const seen = new Map();
      parsed.forEach(l=>{ if(!seen.has(l.label)) seen.set(l.label,l); });
      playerLevels = Array.from(seen.values()).sort((a,b)=>a.height-b.height);
      const pref = getPrefH();
      const chosen = playerLevels.reduce((b,l)=>Math.abs(l.height-pref)<Math.abs(b.height-pref)?l:b, playerLevels[0]);
      hls.currentLevel = chosen.index;
      const bar = document.getElementById('quality-bar');
      bar.innerHTML = `<select class="quality-sel" onchange="changeQ(this)">
        ${playerLevels.map(l=>`<option value="${l.index}"${l.index===chosen.index?' selected':''}>${l.label}</option>`).join('')}
      </select>`;
      video.play().catch(()=>{});
    });
    hls.on(Hls.Events.ERROR,(_, d)=>{
      if(d.fatal){
        const el=document.getElementById('player-err');
        el.textContent=`Playback error: ${d.type}`;
        el.style.display='flex';
      }
    });
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = src;
    video.addEventListener('loadedmetadata', ()=>video.play().catch(()=>{}));
  }
}

function changeQ(sel) {
  const idx = parseInt(sel.value,10);
  if (S.hlsInstance) S.hlsInstance.currentLevel = idx;
  const lvl = playerLevels.find(l=>l.index===idx);
  if (lvl) savePrefH(lvl.height);
}

async function copyStream() {
  const btn = document.getElementById('copy-btn');
  if (!S.activeStream) return;
  try {
    await navigator.clipboard.writeText(S.activeStream);
    const orig = btn.textContent;
    btn.textContent = '✓ Copied!';
    setTimeout(()=>btn.textContent=orig, 1800);
  } catch {}
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s??'')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
    .replace(/'/g,'&#39;');
}

// ─────────────────────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────────────────────
async function init() {
  renderHomeSections();

  // Load hero with trending anime + movies
  try {
    const [anime, movies] = await Promise.all([
      fetch('/api/content/anime/trending').then(r=>r.json()),
      fetch('/api/content/movies/trending').then(r=>r.json()),
    ]);
    const heroItems = [];
    const aSlice = (anime||[]).slice(0,4).map(x=>({...x,type:'anime'}));
    const mSlice = (movies||[]).slice(0,3).map(x=>({...x,type:'movie'}));
    // Interleave
    const maxLen = Math.max(aSlice.length, mSlice.length);
    for (let i=0;i<maxLen;i++) {
      if (aSlice[i]) heroItems.push(aSlice[i]);
      if (mSlice[i]) heroItems.push(mSlice[i]);
    }
    if (heroItems.length) setHero(heroItems.slice(0,7));
  } catch(e) {
    console.warn('Hero load failed', e);
  }
}

// Load section pages lazily
const _origShowSection = showSection;
window.showSection = function(name) {
  _origShowSection(name);
  if (name==='anime') loadAnimePage();
  else if (name==='movies') loadMoviesPage();
  else if (name==='shows') loadShowsPage();
};

init();
</script>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# VIDEASY EXTRACTOR
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
)
ENC_DEC_API = "https://enc-dec.app/api"

VIDEASY_SERVERS = [
    ("mb-flix",    "api"),  ("1movies",    "api"), ("moviebox",   "api"),
    ("cdn",        "api"),  ("primesrcme", "api"), ("primewire",  "api2"),
    ("m4uhd",      "api2"), ("hdmovie",    "api"), ("lamovie",    "api"),
    ("superflix",  "api"),  ("cuevana",    "api2"),("overflix",   "api2"),
    ("visioncine", "api"),  ("meine",      "api"),
]


class ExtractorError(Exception):
    pass


def find_streams(obj):
    found, seen = [], set()
    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                if isinstance(v, str) and v.startswith("http") and v not in seen and (".m3u8" in v or "/master" in v):
                    found.append(v); seen.add(v)
                walk(v)
        elif isinstance(node, list):
            for item in node: walk(item)
    walk(obj)
    return found


async def extract_videasy(player_url: str) -> dict:
    parsed = urlparse(player_url)
    if parsed.netloc.lower() != "player.videasy.net":
        raise ExtractorError("Only player.videasy.net URLs are supported")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ExtractorError("URL must be: https://player.videasy.net/{type}/{tmdb_id}[/{season}/{episode}]")

    media_type = parts[0]
    media_id   = parts[1]

    extra_params = ""
    if media_type in ("tv", "anime") and len(parts) >= 4:
        season  = parts[2]
        episode = parts[3]
        extra_params = f"&season={season}&episode={episode}"
    elif media_type == "anime" and len(parts) >= 3:
        episode = parts[2]
        extra_params = f"&episode={episode}"

    req_headers = {
        "Accept": "*/*",
        "Origin": "https://cineby.sc",
        "Referer": "https://cineby.sc/",
        "User-Agent": DEFAULT_UA,
    }
    errors = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for server, api_sub in VIDEASY_SERVERS:
            api_url = (
                f"https://{api_sub}.videasy.net/{server}/sources-with-title"
                f"?mediaType={media_type}&tmdbId={media_id}{extra_params}"
            )
            print(f"[+] Trying {server} → {api_url}")
            try:
                enc = await client.get(api_url, headers=req_headers)
                if enc.status_code != 200:
                    errors.append(f"{server}: HTTP {enc.status_code}"); continue
                encrypted = enc.text
                if not encrypted or len(encrypted.strip()) < 10:
                    errors.append(f"{server}: empty response"); continue
                dec = await client.post(
                    f"{ENC_DEC_API}/dec-videasy",
                    json={"text": encrypted, "id": str(media_id)},
                    headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": DEFAULT_UA},
                )
                if dec.status_code != 200:
                    errors.append(f"{server}: dec HTTP {dec.status_code}"); continue
                try:
                    dec_data = dec.json()
                except Exception:
                    errors.append(f"{server}: bad JSON"); continue
                if not isinstance(dec_data, dict) or dec_data.get("status") != 200:
                    errors.append(f"{server}: status={dec_data.get('status')}"); continue
                streams = find_streams(dec_data.get("result"))
                if streams:
                    print(f"[+] Got {len(streams)} stream(s) from {server}")
                    return {"tmdb_id": media_id, "server": server, "streams": streams}
                errors.append(f"{server}: no streams")
            except Exception as e:
                errors.append(f"{server}: {e}")
    raise ExtractorError("All servers failed.\n" + "\n".join(errors[-5:]))


# ──────────────────────────────────────────────────────────────────────────────
# TMDB
# ──────────────────────────────────────────────────────────────────────────────

TMDB_BASE  = "https://api.themoviedb.org/3"
TMDB_IMG   = "https://image.tmdb.org/t/p/w500"
TMDB_STILL = "https://image.tmdb.org/t/p/w300"
TMDB_API_KEY_VALUE = os.environ.get("TMDB_API_KEY", "6fad3f86b8452ee232deb7977d7dcf58")

def tmdb_key(): return TMDB_API_KEY_VALUE
def poster(p): return f"{TMDB_IMG}{p}" if p else None
def year(d):   return d[:4] if d else None

async def tmdb_get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{TMDB_BASE}{path}", params={"api_key": tmdb_key(), "language":"en-US", **(params or {})})
        r.raise_for_status(); return r.json()

def tmdb_movie_item(r):
    return {
        "id": r["id"],
        "title": r.get("title") or "Unknown",
        "type": "movie",
        "posterPath": poster(r.get("poster_path")),
        "backdrop": r.get("backdrop_path"),
        "year": year(r.get("release_date")),
        "rating": round(r.get("vote_average", 0), 1) if r.get("vote_average") else None,
        "overview": r.get("overview", ""),
        "episodeCount": None,
    }

def tmdb_tv_item(r):
    return {
        "id": r["id"],
        "title": r.get("name") or "Unknown",
        "type": "tv",
        "posterPath": poster(r.get("poster_path")),
        "backdrop": r.get("backdrop_path"),
        "year": year(r.get("first_air_date")),
        "rating": round(r.get("vote_average", 0), 1) if r.get("vote_average") else None,
        "overview": r.get("overview", ""),
        "episodeCount": None,
    }

async def search_movies(q: str):
    d = await tmdb_get("/search/movie", {"query": q, "page": "1"})
    return [tmdb_movie_item(r) for r in d.get("results", [])[:20]]

async def search_tv(q: str):
    d = await tmdb_get("/search/tv", {"query": q, "page": "1"})
    return [tmdb_tv_item(r) for r in d.get("results", [])[:20]]

async def movies_trending():
    d = await tmdb_get("/trending/movie/week")
    return [tmdb_movie_item(r) for r in d.get("results", [])[:20]]

async def movies_toprated():
    d = await tmdb_get("/movie/top_rated")
    return [tmdb_movie_item(r) for r in d.get("results", [])[:20]]

async def movies_nowplaying():
    d = await tmdb_get("/movie/now_playing")
    return [tmdb_movie_item(r) for r in d.get("results", [])[:20]]

async def shows_trending():
    d = await tmdb_get("/trending/tv/week")
    return [tmdb_tv_item(r) for r in d.get("results", [])[:20]]

async def shows_toprated():
    d = await tmdb_get("/tv/top_rated")
    return [tmdb_tv_item(r) for r in d.get("results", [])[:20]]

async def get_tv_seasons(tmdb_id: int):
    d = await tmdb_get(f"/tv/{tmdb_id}")
    return [
        {"number": s["season_number"], "name": s["name"], "episodeCount": s["episode_count"],
         "posterPath": poster(s.get("poster_path"))}
        for s in d.get("seasons", []) if s["season_number"] > 0
    ]

async def get_tv_episodes(tmdb_id: int, season: int):
    d = await tmdb_get(f"/tv/{tmdb_id}/season/{season}")
    return [
        {"number": e["episode_number"], "name": e["name"],
         "stillPath": f"{TMDB_STILL}{e['still_path']}" if e.get("still_path") else None,
         "overview": e.get("overview") or None}
        for e in d.get("episodes", [])
    ]


# ──────────────────────────────────────────────────────────────────────────────
# ANILIST
# ──────────────────────────────────────────────────────────────────────────────

ANILIST_SEARCH_QUERY = """
query($search:String,$page:Int,$perPage:Int){Page(page:$page,perPage:$perPage){media(search:$search,type:ANIME,sort:SEARCH_MATCH){id idMal title{english romaji}coverImage{large extraLarge}bannerImage startDate{year}episodes averageScore description(asHtml:false)}}}
"""

ANILIST_TRENDING_QUERY = """
query($page:Int,$perPage:Int){Page(page:$page,perPage:$perPage){media(type:ANIME,sort:TRENDING_DESC,status_in:[RELEASING,FINISHED]){id idMal title{english romaji}coverImage{large extraLarge}bannerImage startDate{year}episodes averageScore description(asHtml:false)}}}
"""

ANILIST_TOP_QUERY = """
query($page:Int,$perPage:Int){Page(page:$page,perPage:$perPage){media(type:ANIME,sort:SCORE_DESC){id idMal title{english romaji}coverImage{large extraLarge}bannerImage startDate{year}episodes averageScore description(asHtml:false)}}}
"""

ANILIST_MOVIE_QUERY = """
query($page:Int,$perPage:Int){Page(page:$page,perPage:$perPage){media(type:ANIME,format:MOVIE,sort:POPULARITY_DESC){id idMal title{english romaji}coverImage{large extraLarge}bannerImage startDate{year}episodes averageScore description(asHtml:false)}}}
"""

def _strip_html(s):
    if not s: return ""
    return re.sub(r"<[^>]+>", "", s).strip()

def anilist_item(m):
    title = (m.get("title") or {})
    name = title.get("english") or title.get("romaji") or "Unknown"
    score = m.get("averageScore")
    return {
        "id": m["id"],
        "malId": m.get("idMal"),               # ← MyAnimeList ID (drives MegaPlay/VidWish)
        "title": name,
        "type": "anime",
        "posterPath": (m.get("coverImage") or {}).get("large"),
        "backdrop": m.get("bannerImage"),
        "year": str((m.get("startDate") or {}).get("year")) if (m.get("startDate") or {}).get("year") else None,
        "rating": round(score / 10, 1) if score else None,
        "overview": _strip_html(m.get("description")),
        "episodeCount": m.get("episodes"),
    }

async def anilist_query(query: str, variables: dict) -> list:
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post("https://graphql.anilist.co",
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json", "Accept": "application/json"})
        r.raise_for_status()
    return r.json().get("data", {}).get("Page", {}).get("media", [])

async def anime_trending():
    media = await anilist_query(ANILIST_TRENDING_QUERY, {"page":1,"perPage":20})
    return [anilist_item(m) for m in media]

async def anime_top():
    media = await anilist_query(ANILIST_TOP_QUERY, {"page":1,"perPage":20})
    return [anilist_item(m) for m in media]

async def anime_movies():
    media = await anilist_query(ANILIST_MOVIE_QUERY, {"page":1,"perPage":20})
    return [anilist_item(m) for m in media]

async def search_anime(q: str):
    media = await anilist_query(ANILIST_SEARCH_QUERY, {"search":q,"page":1,"perPage":20})
    return [anilist_item(m) for m in media]


# ──────────────────────────────────────────────────────────────────────────────
# FASTAPI APP
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="StreamVault Pro")

class ExtractRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=HTML)

@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}

# ── Content endpoints ────────────────────────────────────────────────────────
@app.get("/api/content/anime/trending")
async def ct_anime_trend():
    try: return await anime_trending()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/content/anime/top")
async def ct_anime_top():
    try: return await anime_top()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/content/anime/movies")
async def ct_anime_movies():
    try: return await anime_movies()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

# ─────────────────────────────────────────────────────────────────
# MAL / Jikan resolver — maps an AniList id (and/or title) to a
# MyAnimeList id and authoritative episode count. The frontend hits
# this endpoint when AniList didn't provide `idMal`, so the
# MegaPlay/VidWish players (which use MAL ids) can still play.
# ─────────────────────────────────────────────────────────────────
JIKAN_BASE = "https://api.jikan.moe/v4"

ANILIST_BY_ID_QUERY = """
query($id:Int){Media(id:$id,type:ANIME){id idMal episodes}}
"""

async def jikan_get(path: str) -> dict:
    """Tiny Jikan GET helper with sane timeout / error handling."""
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.get(f"{JIKAN_BASE}{path}",
                        headers={"Accept": "application/json"})
        if r.status_code >= 400:
            return {}
        try: return r.json()
        except Exception: return {}

@app.get("/api/anime/resolve")
async def anime_resolve(anilist_id: int | None = None,
                        title:       str | None = None):
    """
    Return {malId, episodes, title} for the requested anime.
    Resolution order:
      1) AniList Media(id) → idMal + episodes  (fastest, single round-trip)
      2) Jikan /anime?q=<title>                (fallback when AniList lacks idMal)
    """
    mal_id, episodes, resolved_title = None, None, None

    # ─ Step 1: AniList by id ─
    if anilist_id:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post("https://graphql.anilist.co",
                    json={"query": ANILIST_BY_ID_QUERY,
                          "variables": {"id": int(anilist_id)}},
                    headers={"Content-Type": "application/json"})
                if r.status_code < 400:
                    m = (r.json().get("data") or {}).get("Media") or {}
                    mal_id   = m.get("idMal")
                    episodes = m.get("episodes")
        except Exception:
            pass

    # ─ Step 2: Jikan by title (only if still missing MAL id) ─
    if not mal_id and title:
        try:
            from urllib.parse import quote
            data = await jikan_get(f"/anime?q={quote(title)}&limit=1")
            arr = (data or {}).get("data") or []
            if arr:
                top = arr[0]
                mal_id   = top.get("mal_id")
                episodes = episodes or top.get("episodes")
                resolved_title = top.get("title_english") or top.get("title")
        except Exception:
            pass

    # ─ Optional Step 3: enrich episodes when we have a MAL id but no count ─
    if mal_id and not episodes:
        try:
            data = await jikan_get(f"/anime/{mal_id}")
            d = (data or {}).get("data") or {}
            episodes = d.get("episodes") or episodes
            resolved_title = resolved_title or d.get("title_english") or d.get("title")
        except Exception:
            pass

    return {"malId": mal_id, "episodes": episodes, "title": resolved_title}

@app.get("/api/anime/jikan/{mal_id}")
async def anime_jikan_details(mal_id: int):
    """Direct Jikan passthrough for an individual MAL id."""
    data = await jikan_get(f"/anime/{mal_id}")
    d = (data or {}).get("data") or {}
    if not d:
        raise HTTPException(404, {"error": "MAL id not found on Jikan"})
    return {
        "malId":    d.get("mal_id"),
        "title":    d.get("title_english") or d.get("title"),
        "episodes": d.get("episodes"),
        "score":    d.get("score"),
        "year":     d.get("year"),
        "status":   d.get("status"),
        "synopsis": d.get("synopsis"),
        "image":    (d.get("images", {}).get("jpg") or {}).get("large_image_url"),
    }

@app.get("/api/content/movies/trending")
async def ct_movies_trend():
    try: return await movies_trending()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/content/movies/toprated")
async def ct_movies_top():
    try: return await movies_toprated()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/content/movies/nowplaying")
async def ct_movies_now():
    try: return await movies_nowplaying()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/content/shows/trending")
async def ct_shows_trend():
    try: return await shows_trending()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/content/shows/toprated")
async def ct_shows_top():
    try: return await shows_toprated()
    except Exception as e: raise HTTPException(502, {"error": str(e)})

# ── Extract ──────────────────────────────────────────────────────────────────
@app.post("/api/streams/extract")
async def api_extract(body: ExtractRequest):
    try:
        result = await extract_videasy(body.url)
        return {"tmdbId": result["tmdb_id"], "server": result["server"], "streams": result["streams"]}
    except ExtractorError as e:
        msg = str(e)
        code = 400 if any(msg.startswith(x) for x in ("Only player","URL must")) else 502
        raise HTTPException(status_code=code, detail={"error": msg})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── Media search ─────────────────────────────────────────────────────────────
@app.get("/api/media/search")
async def api_search(q: str = Query(...), type: str = Query(...)):
    try:
        if type == "movie":   return await search_movies(q)
        elif type == "tv":    return await search_tv(q)
        elif type == "anime": return await search_anime(q)
        raise HTTPException(400, {"error": "type must be movie|tv|anime"})
    except HTTPException: raise
    except Exception as e: raise HTTPException(502, {"error": str(e)})

@app.get("/api/media/tv/{tmdb_id}/seasons")
async def api_seasons(tmdb_id: int):
    try: return await get_tv_seasons(tmdb_id)
    except Exception as e: raise HTTPException(404, {"error": str(e)})

@app.get("/api/media/tv/{tmdb_id}/seasons/{season}/episodes")
async def api_episodes(tmdb_id: int, season: int):
    try: return await get_tv_episodes(tmdb_id, season)
    except Exception as e: raise HTTPException(404, {"error": str(e)})


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"""
╔══════════════════════════════════════════════════════╗
║         StreamVault Pro — Streaming Extractor        ║
╠══════════════════════════════════════════════════════╣
║  Open:  http://localhost:{port:<28}║
║  TMDB:  Set TMDB_API_KEY env var for best results    ║
╚══════════════════════════════════════════════════════╝
""")
    uvicorn.run(app, host="0.0.0.0", port=port)
