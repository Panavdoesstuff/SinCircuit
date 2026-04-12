"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";

// ─────────────────────────────────────────────────────────────────────────────
//  Types
// ─────────────────────────────────────────────────────────────────────────────
type ChatMsg = { role: "user" | "assistant"; content: string };
type Genre = {
  genre: string; icon: string; color: string;
  sports: string[];
  best_sites: { name: string; url: string; reason: string; bonus: string; pro_tip: string }[];
};

// ─────────────────────────────────────────────────────────────────────────────
//  Card constants
// ─────────────────────────────────────────────────────────────────────────────
const RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"];
const SUITS = ["s", "h", "d", "c"];
const SUIT_GLYPHS: Record<string, string> = { s: "♠", h: "♥", d: "♦", c: "♣" };
const SUIT_RED: Record<string, boolean> = { s: false, h: true, d: true, c: false };

function cardId(rank: string, suit: string) {
  return rank === "T" ? `10${suit}` : `${rank}${suit}`;
}
function suitGlyph(suit: string) { return SUIT_GLYPHS[suit] ?? suit; }
function isRedSuit(suit: string) { return SUIT_RED[suit] ?? false; }

function rankValue(rank: string): number {
  if (["J", "Q", "K"].includes(rank)) return 10;
  if (rank === "A") return 11;
  if (rank === "T") return 10;
  return parseInt(rank, 10);
}

function bjTotal(cards: { rank: string; suit: string }[]): number {
  let total = 0, aces = 0;
  for (const c of cards) {
    const v = rankValue(c.rank);
    total += v;
    if (c.rank === "A") aces++;
  }
  while (total > 21 && aces > 0) { total -= 10; aces--; }
  return total;
}

// ─────────────────────────────────────────────────────────────────────────────
//  Rich Playing Card Component
// ─────────────────────────────────────────────────────────────────────────────
function PlayingCard({
  rank, suit,
  size = "picker",
  variant = "normal",
  onClick,
  disabled,
  animateIn = false,
}: {
  rank: string; suit: string;
  size?: "picker" | "hand" | "large";
  variant?: "normal" | "selected" | "community" | "disabled" | "dealer";
  onClick?: () => void;
  disabled?: boolean;
  animateIn?: boolean;
}) {
  const red = isRedSuit(suit);
  const glyph = suitGlyph(suit);
  const displayRank = rank === "T" ? "10" : rank;

  // Size classes
  const sizes = {
    picker: { w: 52, h: 74, rankSize: "12px", suitBig: "20px", cornerSize: "10px" },
    hand: { w: 68, h: 96, rankSize: "15px", suitBig: "28px", cornerSize: "12px" },
    large: { w: 80, h: 112, rankSize: "17px", suitBig: "34px", cornerSize: "14px" },
  };
  const sz = sizes[size];

  const suitColor = red ? "#dc2626" : "#0f172a";
  const bgColor = variant === "disabled" ? "#d1d5db" : "#ffffff";

  let borderStyle = "2px solid rgba(0,0,0,0.12)";
  let boxShadow = "0 4px 14px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.3)";
  let transform = "none";
  let cursor = onClick ? "pointer" : "default";

  if (variant === "selected") {
    borderStyle = "2.5px solid #e5383b";
    boxShadow = "0 0 0 3px rgba(229,56,59,0.4), 0 8px 24px rgba(229,56,59,0.3), 0 4px 14px rgba(0,0,0,0.5)";
    transform = "translateY(-10px) scale(1.05)";
  } else if (variant === "community") {
    borderStyle = "2.5px solid #3b82f6";
    boxShadow = "0 0 0 3px rgba(59,130,246,0.4), 0 8px 24px rgba(59,130,246,0.3), 0 4px 14px rgba(0,0,0,0.5)";
    transform = "translateY(-8px) scale(1.04)";
  } else if (variant === "dealer") {
    borderStyle = "2.5px solid #f97316";
    boxShadow = "0 0 0 3px rgba(249,115,22,0.4), 0 8px 24px rgba(249,115,22,0.3), 0 4px 14px rgba(0,0,0,0.5)";
    transform = "translateY(-6px) scale(1.03)";
  } else if (variant === "disabled") {
    cursor = "not-allowed";
    boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
  }

  return (
    <div
      onClick={!disabled ? onClick : undefined}
      role={onClick ? "button" : undefined}
      style={{
        width: sz.w, height: sz.h,
        background: bgColor,
        borderRadius: 8,
        border: borderStyle,
        boxShadow,
        transform,
        cursor,
        position: "relative",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "4px 5px",
        flexShrink: 0,
        userSelect: "none",
        transition: "transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease",
        opacity: variant === "disabled" ? 0.4 : 1,
        fontFamily: "'Georgia', serif",
        fontWeight: 700,
      }}
    >
      {/* Top-left corner */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", lineHeight: 1.1 }}>
        <span style={{ fontSize: sz.rankSize, color: suitColor, fontWeight: 800 }}>{displayRank}</span>
        <span style={{ fontSize: sz.cornerSize, color: suitColor, lineHeight: 1 }}>{glyph}</span>
      </div>

      {/* Center suit — large */}
      <div style={{
        position: "absolute", top: "50%", left: "50%",
        transform: "translate(-50%,-50%)",
        fontSize: sz.suitBig, color: suitColor, lineHeight: 1,
        textShadow: red ? "0 0 8px rgba(220,38,38,0.2)" : "none",
      }}>
        {glyph}
      </div>

      {/* Bottom-right corner (rotated) */}
      <div style={{
        display: "flex", flexDirection: "column", alignItems: "flex-end",
        transform: "rotate(180deg)", lineHeight: 1.1,
      }}>
        <span style={{ fontSize: sz.rankSize, color: suitColor, fontWeight: 800 }}>{displayRank}</span>
        <span style={{ fontSize: sz.cornerSize, color: suitColor, lineHeight: 1 }}>{glyph}</span>
      </div>
    </div>
  );
}

/** Card back (face down) */
function CardBack({ size = "hand" }: { size?: "hand" | "large" }) {
  const w = size === "large" ? 80 : 68;
  const h = size === "large" ? 112 : 96;
  return (
    <div style={{
      width: w, height: h,
      borderRadius: 8,
      background: "linear-gradient(135deg, #1e3a8a, #1e40af, #1d4ed8)",
      border: "3px solid #fff",
      boxShadow: "0 4px 14px rgba(0,0,0,0.55)",
      display: "flex", alignItems: "center", justifyContent: "center",
      flexShrink: 0, position: "relative", overflow: "hidden",
    }}>
      {/* Decorative pattern */}
      <div style={{
        position: "absolute", inset: 4,
        border: "1px solid rgba(255,255,255,0.2)",
        borderRadius: 4,
        background: "repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(255,255,255,0.04) 4px, rgba(255,255,255,0.04) 8px)",
      }} />
      <span style={{ fontSize: 22, zIndex: 1 }}>🂠</span>
    </div>
  );
}

/** Decision badge */
function DecisionBadge({ d }: { d: string }) {
  if (d === "STRONG BET") return <span className="badge-value">⚡ STRONG BET</span>;
  if (d === "BET") return <span className="badge-arb">◆ BET</span>;
  if (d === "VALUE") return <span className="badge-value">★ VALUE</span>;

  const styles: Record<string, { bg: string; color: string; border: string }> = {
    "NO BET": { bg: "rgba(148,163,184,0.1)", color: "#94a3b8", border: "rgba(148,163,184,0.2)" },
    "RAISE": { bg: "rgba(0,255,136,0.15)", color: "var(--neon-green)", border: "rgba(0,255,136,0.3)" },
    "CALL": { bg: "rgba(0,212,255,0.15)", color: "var(--neon-blue)", border: "rgba(0,212,255,0.3)" },
    "FOLD": { bg: "rgba(255,77,109,0.15)", color: "var(--neon-red)", border: "rgba(255,77,109,0.3)" },
    "CHECK": { bg: "rgba(192,132,252,0.15)", color: "var(--neon-purple)", border: "rgba(192,132,252,0.3)" },
    "STAND": { bg: "rgba(0,255,136,0.15)", color: "var(--neon-green)", border: "rgba(0,255,136,0.3)" },
    "HIT": { bg: "rgba(0,212,255,0.15)", color: "var(--neon-blue)", border: "rgba(0,212,255,0.3)" },
    "DOUBLE": { bg: "rgba(251,191,36,0.15)", color: "var(--neon-gold)", border: "rgba(251,191,36,0.3)" },
  };
  const s = styles[d] ?? { bg: "rgba(148,163,184,0.1)", color: "#94a3b8", border: "rgba(148,163,184,0.2)" };
  return (
    <span style={{
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      borderRadius: 9999, padding: "3px 12px",
      fontSize: 11, fontWeight: 700, whiteSpace: "nowrap", fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.05em"
    }}>
      {d}
    </span>
  );
}

/** Typing indicator */
function TypingIndicator() {
  return (
    <div className="chat-bubble-ai" style={{ display: "flex", alignItems: "center", gap: 5, width: "fit-content" }}>
      {[0, 0.2, 0.4].map((d, i) => (
        <div key={i} className="typing-dot" style={{ animationDelay: `${d}s` }} />
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Card Picker Grid
// ─────────────────────────────────────────────────────────────────────────────
function CardPickerGrid({
  holeSelected, communitySelected,
  bjMode, bjPlayerCards, bjDealerCard,
  mode,
  maxHole = 2, maxCommunity = 5,
  onHoleToggle, onCommunityToggle,
  onBjClick,
}: {
  holeSelected?: Set<string>;
  communitySelected?: Set<string>;
  bjMode?: "player" | "dealer";
  bjPlayerCards?: { rank: string; suit: string }[];
  bjDealerCard?: { rank: string; suit: string } | null;
  mode: "poker" | "blackjack";
  maxHole?: number; maxCommunity?: number;
  onHoleToggle?: (id: string) => void;
  onCommunityToggle?: (id: string) => void;
  onBjClick?: (rank: string, suit: string) => void;
}) {
  return (
    <div style={{ overflowX: "auto", paddingBottom: 8 }}>
      {SUITS.map(suit => (
        <div key={suit} style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 4, flexWrap: "nowrap" }}>
          <span style={{
            fontSize: 18, width: 22, textAlign: "center", flexShrink: 0,
            color: isRedSuit(suit) ? "#dc2626" : "#e2e8f0",
          }}>
            {suitGlyph(suit)}
          </span>

          {RANKS.map(rank => {
            const id = cardId(rank, suit);

            if (mode === "blackjack") {
              const inP = bjPlayerCards?.some(c => cardId(c.rank, c.suit) === id) ?? false;
              const inD = bjDealerCard ? cardId(bjDealerCard.rank, bjDealerCard.suit) === id : false;
              const used = inP || inD;
              return (
                <PlayingCard
                  key={id} rank={rank} suit={suit} size="picker"
                  variant={
                    bjMode === "player" && inP ? "selected" :
                      bjMode === "dealer" && inD ? "dealer" :
                        used ? "disabled" : "normal"
                  }
                  disabled={used && !(bjMode === "player" ? inP : inD)}
                  onClick={() => onBjClick?.(rank, suit)}
                />
              );
            }

            // Poker mode
            const inH = holeSelected?.has(id) ?? false;
            const inC = communitySelected?.has(id) ?? false;
            const holeFull = (holeSelected?.size ?? 0) >= maxHole && !inH;
            const commFull = (communitySelected?.size ?? 0) >= maxCommunity && !inC;
            const taken = inH || inC;

            return (
              <PlayingCard
                key={id} rank={rank} suit={suit} size="picker"
                variant={inH ? "selected" : inC ? "community" : taken ? "disabled" : "normal"}
                disabled={!taken && holeFull && commFull}
                onClick={() => {
                  if (inH) { onHoleToggle?.(id); return; }
                  if (inC) { onCommunityToggle?.(id); return; }
                  if (!holeFull) onHoleToggle?.(id);
                  else if (!commFull) onCommunityToggle?.(id);
                }}
              />
            );
          })}
        </div>
      ))}
      {mode === "poker" && (
        <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#94a3b8", marginTop: 4 }}>
          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#e5383b", display: "inline-block" }} />
            Hole cards
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#3b82f6", display: "inline-block" }} />
            Community
          </span>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Genre Accordion
// ─────────────────────────────────────────────────────────────────────────────
function GenreCard({ genre }: { genre: Genre }) {
  const [open, setOpen] = useState(false);
  const [siteExpanded, setSiteExpanded] = useState<number | null>(null);

  return (
    <div className="genre-card">
      <div className="genre-header" onClick={() => setOpen(o => !o)}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 22 }}>{genre.icon}</span>
          <span style={{ fontWeight: 700, fontSize: 15, color: "#e2e8f0" }}>{genre.genre}</span>
          <span style={{ fontSize: 11, color: "#475569" }}>
            {genre.sports.length} sports · {genre.best_sites.length} top sites
          </span>
        </div>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }} style={{ color: "#64748b", fontSize: 18 }}>
          ▾
        </motion.span>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            style={{ overflow: "hidden" }}
          >
            <div style={{ padding: "0 16px 16px", display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Sports chips */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {genre.sports.map(s => (
                  <span key={s} style={{
                    fontSize: 11, padding: "3px 10px", borderRadius: 999,
                    background: `${genre.color}14`, color: genre.color,
                    border: `1px solid ${genre.color}30`,
                  }}>
                    {s}
                  </span>
                ))}
              </div>

              {/* Best sites */}
              <div>
                <p style={{ fontSize: 10, color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8, fontWeight: 700 }}>
                  Best Sites to Bet — For Maximum Profit
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {genre.best_sites.map((site, i) => (
                    <div key={site.name} style={{
                      borderRadius: 10, border: "1px solid rgba(255,255,255,0.06)",
                      background: "rgba(255,255,255,0.02)", overflow: "hidden",
                    }}>
                      <button
                        style={{
                          width: "100%", display: "flex", alignItems: "center",
                          justifyContent: "space-between", padding: "10px 14px",
                          background: "transparent", border: "none", cursor: "pointer",
                        }}
                        onClick={() => setSiteExpanded(siteExpanded === i ? null : i)}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span style={{
                            width: 22, height: 22, borderRadius: "50%",
                            background: genre.color + "25", border: `1px solid ${genre.color}50`,
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 11, fontWeight: 800, color: genre.color, flexShrink: 0,
                          }}>
                            {i + 1}
                          </span>
                          <span style={{ fontWeight: 700, fontSize: 13, color: "#e2e8f0" }}>{site.name}</span>
                          <span style={{
                            fontSize: 10, padding: "2px 7px", borderRadius: 999,
                            background: "#022c22", color: "#4ade80", border: "1px solid #166534",
                            display: "inline-block",
                          }}>
                            🎁 {site.bonus}
                          </span>
                        </div>
                        <span style={{ color: "#475569", fontSize: 13 }}>{siteExpanded === i ? "▴" : "▾"}</span>
                      </button>

                      <AnimatePresence>
                        {siteExpanded === i && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            style={{ overflow: "hidden" }}
                          >
                            <div style={{
                              padding: "10px 14px 14px", borderTop: "1px solid rgba(255,255,255,0.05)",
                              display: "flex", flexDirection: "column", gap: 8,
                            }}>
                              <p style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.6 }}>{site.reason}</p>
                              <p style={{
                                fontSize: 12, padding: "6px 10px", borderRadius: 7,
                                background: "rgba(251,191,36,0.07)", color: "#fbbf24",
                                borderLeft: "3px solid rgba(251,191,36,0.4)",
                              }}>
                                💡 <strong>Pro tip:</strong> {site.pro_tip}
                              </p>
                              <a
                                href={site.url} target="_blank" rel="noopener noreferrer"
                                style={{
                                  display: "inline-flex", alignItems: "center", gap: 5,
                                  fontSize: 12, padding: "7px 14px", borderRadius: 8,
                                  background: genre.color + "15",
                                  border: `1px solid ${genre.color}40`,
                                  color: genre.color, fontWeight: 600,
                                  textDecoration: "none", alignSelf: "flex-start",
                                  transition: "background 0.2s",
                                }}
                              >
                                Visit {site.name} →
                              </a>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Main Component
// ─────────────────────────────────────────────────────────────────────────────
export default function Home() {
  const [tab, setTab] = useState("sportsbook");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Sportsbook
  const [genres, setGenres] = useState<Genre[]>([]);
  const [genresLoading, setGenresLoading] = useState(false);

  // ── Blackjack
  const [bjPlayerCards, setBjPlayerCards] = useState<{ rank: string; suit: string }[]>([]);
  const [bjDealerCard, setBjDealerCard] = useState<{ rank: string; suit: string } | null>(null);
  const [bjResult, setBjResult] = useState("");
  const [bjLoading, setBjLoading] = useState(false);
  const [bjMode, setBjMode] = useState<"player" | "dealer">("player");

  // ── Poker v2
  const [holeSet, setHoleSet] = useState<Set<string>>(new Set());
  const [communitySet, setCommunitySet] = useState<Set<string>>(new Set());
  const [potSize, setPotSize] = useState(100);
  const [callAmt, setCallAmt] = useState(20);
  const [oppBet, setOppBet] = useState(0);
  const [numOpponents, setNumOpponents] = useState(1);
  const [pokerResult, setPokerResult] = useState<any>(null);
  const [pokerLoading, setPokerLoading] = useState(false);

  // ── Strategy chat
  const [chatHistory, setChatHistory] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ── Search & Suggestions
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<{ matches: any[], sites: any[], genres: any[], ai_answer: string, is_betting_related: boolean | null, intent: string } | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const fetchSuggestions = async (q: string) => {
    try {
      const res = await fetch(`${API}/suggestions?q=${encodeURIComponent(q)}`);
      const json = await res.json();
      setSuggestions(json.suggestions || []);
    } catch { setSuggestions([]); }
  };

  const runSearch = async (q: string) => {
    if (!q.trim()) return;
    setSearchLoading(true);
    setSuggestions([]);
    try {
      const res = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
      const json = await res.json();
      setSearchResults({
        matches: json.matches || [],
        sites: json.sites || [],
        genres: json.genres || [],
        ai_answer: json.ai_answer || "",
        is_betting_related: json.is_betting_related ?? null,
        intent: json.intent || "general",
      });
    } catch {
      setSearchResults({ matches: [], sites: [], genres: [], ai_answer: "", is_betting_related: null, intent: "general" });
    }
    setSearchLoading(false);
  };

  const STARTERS = [
    "How do I apply Kelly Criterion to my bets?",
    "What's the best poker move with a flush draw?",
    "How do I find value bets in cricket?",
    "Explain arbitrage betting to me",
    "When should I stand in blackjack?",
    "How much of my bankroll should I risk per bet?",
  ];

  // ── Fetch main data on mount
  useEffect(() => {
    fetch(`${API}/full-system`)
      .then(r => { if (!r.ok) throw new Error("Backend not responding"); return r.json(); })
      .then(setData)
      .catch(() => setError("Could not connect to backend. Make sure it is running on port 8001."));
  }, []);

  // ── Count Up Animation for Odds
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target as HTMLElement;
          if (el.dataset.counted === "true") return;
          el.dataset.counted = "true";
          const finalValStr = el.innerText.replace(/[^0-9.-]/g, '');
          const finalVal = parseFloat(finalValStr);
          if (isNaN(finalVal)) return;
          
          const isDec = el.innerText.includes('.');
          
          const duration = 1200;
          const startTime = performance.now();
          
          const step = (now: number) => {
            const progress = Math.min((now - startTime) / duration, 1);
            const easeOut = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const current = (finalVal * easeOut).toFixed(isDec ? 2 : 0);
            const prefix = el.innerText.includes('+') && !current.startsWith('-') ? '+' : '';
            el.innerText = prefix + current;
            if (progress < 1) requestAnimationFrame(step);
            else el.innerText = prefix + (isDec ? finalVal.toFixed(2) : finalVal.toString());
          };
          requestAnimationFrame(step);
        }
      });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.odds-pill, .badge-value').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, [data, searchResults]);

  // ── Fetch genres when sportsbook tab opens
  useEffect(() => {
    if (tab !== "sportsbook" || genres.length) return;
    setGenresLoading(true);
    fetch(`${API}/sports-by-genre`)
      .then(r => r.json())
      .then(d => setGenres(d.genres ?? []))
      .catch(() => { })
      .finally(() => setGenresLoading(false));
  }, [tab]);

  // ── Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, chatLoading]);

  // ── Blackjack handlers
  const bjAllCards = [...bjPlayerCards, ...(bjDealerCard ? [bjDealerCard] : [])];
  const bjUsed = new Set(bjAllCards.map(c => cardId(c.rank, c.suit)));

  const handleBjCardClick = (rank: string, suit: string) => {
    const id = cardId(rank, suit);
    if (bjMode === "player") {
      if (bjPlayerCards.some(c => cardId(c.rank, c.suit) === id)) {
        setBjPlayerCards(prev => prev.filter(c => cardId(c.rank, c.suit) !== id));
      } else if (bjPlayerCards.length < 6 && !bjUsed.has(id)) {
        setBjPlayerCards(prev => [...prev, { rank, suit }]);
      }
    } else {
      if (bjDealerCard && cardId(bjDealerCard.rank, bjDealerCard.suit) === id) {
        setBjDealerCard(null);
      } else if (!bjUsed.has(id)) {
        setBjDealerCard({ rank, suit });
      }
    }
  };

  const runBlackjack = async () => {
    if (!bjDealerCard || bjPlayerCards.length < 2) return;
    setBjLoading(true); setBjResult("");
    const total = bjTotal(bjPlayerCards);
    const dealer = rankValue(bjDealerCard.rank);
    try {
      const res = await fetch(`${API}/blackjack?player_total=${total}&dealer_card=${dealer}`);
      const json = await res.json();
      setBjResult(json.decision);
    } catch { setBjResult("Error connecting to server."); }
    setBjLoading(false);
  };

  // ── Poker handlers
  const toggleHole = (id: string) => {
    setHoleSet(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else if (next.size < 2) next.add(id);
      return next;
    });
    setPokerResult(null);
  };
  const toggleCommunity = (id: string) => {
    setCommunitySet(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else if (next.size < 5) next.add(id);
      return next;
    });
    setPokerResult(null);
  };

  const runPoker = async () => {
    if (holeSet.size < 2) return;
    setPokerLoading(true); setPokerResult(null);
    try {
      const res = await fetch(`${API}/poker-v2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          your_cards: Array.from(holeSet),
          community_cards: Array.from(communitySet),
          pot_size: potSize,
          call_amount: callAmt,
          opponents_total_bet: oppBet,
          num_opponents: numOpponents,
        }),
      });
      setPokerResult(await res.json());
    } catch { setPokerResult({ decision: "ERROR", advice: "Server error." }); }
    setPokerLoading(false);
  };

  // ── Chat handler
  const sendChat = async (msg?: string) => {
    const text = (msg ?? chatInput).trim();
    if (!text || chatLoading) return;
    setChatInput("");
    const userMsg: ChatMsg = { role: "user", content: text };
    setChatHistory(h => [...h, userMsg]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: chatHistory }),
      });
      const json = await res.json();
      setChatHistory(h => [...h, { role: "assistant", content: json.reply }]);
    } catch {
      setChatHistory(h => [...h, { role: "assistant", content: "Sorry, I couldn't reach the AI engine. Please ensure the backend is running." }]);
    }
    setChatLoading(false);
  };

  const cardFromId = (id: string) => {
    const is10 = id.startsWith("10");
    const rank = is10 ? "T" : id[0].toUpperCase();
    const suit = is10 ? id[2] : id[1];
    return { rank, suit };
  };

  // ─────────────────────────────────────────────
  //  Error / Loading
  // ─────────────────────────────────────────────
  if (error) return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24, textAlign: "center" }}>
      <div style={{ fontSize: 52, marginBottom: 16 }}>⚠️</div>
      <h2 style={{ color: "#f87171", fontSize: 22, fontWeight: 800, marginBottom: 12 }}>Connection Error</h2>
      <p style={{ color: "#94a3b8", maxWidth: 400, marginBottom: 24 }}>{error}</p>
      <button className="btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
    </div>
  );

  if (error) return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24, padding: 20, textAlign: "center" }}>
      <div style={{ fontSize: 64 }}>📡</div>
      <h1 style={{ color: "var(--neon-gold)", fontSize: 24, fontWeight: 800 }}>CONNECTION INTERRUPTED</h1>
      <p style={{ color: "var(--text-secondary)", maxWidth: 400, lineHeight: 1.6 }}>{error}</p>
      <button 
        onClick={() => window.location.reload()}
        className="btn-primary"
        style={{ marginTop: 12 }}
      >
        RETRY CONNECTION
      </button>
    </div>
  );

  if (!data) return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16 }}>
      <div style={{ fontSize: 48 }}>🎰</div>
      <div style={{ color: "var(--neon-gold)", fontSize: 18, fontWeight: 800 }} className="animate-pulse">SYNCHRONIZING BETSMART AI…</div>
      <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>Fetching real-time market data...</p>
    </div>
  );

  // ─────────────────────────────────────────────
  //  Main Render
  // ─────────────────────────────────────────────
  return (
    <div className="min-h-screen">

      {/* ── HEADER ───────────────────────────────── */}
      <header style={{
        position: "sticky", top: 0, zIndex: 50,
        background: "rgba(8,11,16,0.55)", backdropFilter: "blur(24px)",
        WebkitBackdropFilter: "blur(24px)", borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "12px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h1 style={{ fontSize: 22, fontWeight: 900, letterSpacing: "-0.02em" }} className="header-glow">🎰 BetSmart AI</h1>
          <nav style={{ display: "flex", gap: 8 }}>
            {(["sportsbook", "casino", "strategy"] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`nav-tab ${tab === t ? "nav-tab-active" : "nav-tab-inactive"}`}
              >
                {t === "sportsbook" ? "📊 SPORTSBOOK" : t === "casino" ? "🃏 CASINO" : "🧠 STRATEGY"}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main style={{ maxWidth: 1060, margin: "0 auto", padding: "32px 16px" }}>

        {/* ══════════════════════════════════════════════════
            SPORTSBOOK TAB
        ══════════════════════════════════════════════════ */}
        {tab === "sportsbook" && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: 40 }}>

            {/* 🔍 Universal AI Search Bar */}
            <section style={{ position: "relative", zIndex: 60 }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                <h2 style={{ fontSize: 20, fontWeight: 800, color: "#fff", display: "flex", alignItems: "center", gap: 8 }}>
                  🔍 AI Sports Betting Search
                </h2>
                <span style={{ fontSize: 11, background: "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(59,130,246,0.2))", padding: "3px 10px", borderRadius: 6, color: "#a78bfa", fontWeight: 700, border: "1px solid rgba(124,58,237,0.3)" }}>
                  ⚡ Groq AI Powered
                </span>
              </div>
              <p style={{ fontSize: 13, color: "#64748b", marginBottom: 16 }}>Search anything — teams, leagues, bookmakers, bet types. AI filters non-betting queries automatically.</p>

              <div style={{ position: "relative" }}>
                <div style={{ display: "flex", gap: 8 }}>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="e.g. 'Real Madrid odds', 'best NBA value bets', 'DraftKings cricket'..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      if (e.target.value.length >= 2) fetchSuggestions(e.target.value);
                      else setSuggestions([]);
                    }}
                    onKeyDown={(e) => e.key === "Enter" && runSearch(searchQuery)}
                    style={{
                      flex: 1,
                      padding: "16px 20px",
                      background: "rgba(13,22,40,0.6)",
                      border: "2px solid rgba(0,212,255,0.2)",
                      borderRadius: 14,
                      color: "var(--text-primary)",
                      fontSize: 15,
                      outline: "none",
                      fontFamily: "Inter, sans-serif",
                      transition: "all 0.2s",
                      boxShadow: "0 8px 32px rgba(0,0,0,0.4)"
                    }}
                  />
                  <button
                    onClick={() => runSearch(searchQuery)}
                    disabled={searchLoading || !searchQuery.trim()}
                    className="btn-neon-blue"
                    style={{
                      padding: "0 28px",
                      height: "100%",
                      fontSize: 15,
                      letterSpacing: "0.05em",
                      borderWidth: 2,
                      cursor: searchLoading || !searchQuery.trim() ? "not-allowed" : "pointer",
                      opacity: !searchQuery.trim() ? 0.5 : 1,
                      whiteSpace: "nowrap", flexShrink: 0,
                    }}
                  >
                    {searchLoading ? "SEARCHING..." : "SEARCH 🔍"}
                  </button>
                </div>

                {/* Suggestions Dropdown */}
                <AnimatePresence>
                  {suggestions.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      style={{
                        position: "absolute", top: "100%", left: 0, right: 0,
                        background: "#111827",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "0 0 14px 14px",
                        marginTop: 1, overflow: "hidden", zIndex: 100,
                        boxShadow: "0 12px 48px rgba(0,0,0,0.5)"
                      }}
                    >
                      {suggestions.map((s, i) => (
                        <div
                          key={i}
                          className="suggestion-item"
                          onClick={() => {
                            setSearchQuery(s);
                            setSuggestions([]);
                            runSearch(s);
                          }}
                          style={{
                            padding: "12px 20px",
                            cursor: "pointer",
                            fontSize: 14,
                            color: "#94a3b8",
                            borderBottom: i < suggestions.length - 1 ? "1px solid rgba(255,255,255,0.03)" : "none",
                            display: "flex",
                            alignItems: "center",
                            gap: 10
                          }}
                        >
                          <span style={{ fontSize: 12 }}>⚡</span> {s}
                        </div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Trouble Connecting Warning */}
              <div style={{
                marginTop: 16,
                padding: "12px 16px",
                background: "rgba(251,191,36,0.04)",
                border: "1px solid rgba(251,191,36,0.15)",
                borderRadius: 10,
                display: "flex",
                alignItems: "center",
                gap: 12
              }}>
                <span style={{ fontSize: 20 }}>🛡️</span>
                <div>
                  <p style={{ fontSize: 13, color: "#fbbf24", fontWeight: 700, marginBottom: 2 }}>Regional Access Guidance</p>
                  <p style={{ fontSize: 12, color: "#94a3b8" }}>
                    Some bookmakers like <strong>DraftKings</strong> and <strong>FanDuel</strong> are restricted to the US/Canada.
                    If you see a <span style={{ color: "#f87171", fontWeight: 700 }}>Region Locked</span> badge, you may need a US-ready connection.
                  </p>
                </div>
              </div>
            </section>

            {/* 📊 AI-Powered Search Results Section */}
            {searchResults !== null && (
              <section className="fade-in">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                  <h2 style={{ fontSize: 20, fontWeight: 800, color: "#fff", display: "flex", alignItems: "center", gap: 8 }}>
                    ✨ {searchLoading ? "Searching..." : "Search Results"}
                  </h2>
                  <button
                    onClick={() => { setSearchResults(null); setSearchQuery(""); }}
                    style={{ background: "transparent", border: "none", color: "#64748b", fontSize: 13, cursor: "pointer", fontWeight: 600 }}
                  >
                    Clear ✕
                  </button>
                </div>

                {/* Not betting related state */}
                {searchResults.is_betting_related === false && (
                  <div style={{
                    padding: "40px 24px", textAlign: "center",
                    background: "rgba(255,255,255,0.02)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    borderRadius: 16,
                  }}>
                    <div style={{ fontSize: 48, marginBottom: 12 }}>🔍</div>
                    <p style={{ fontSize: 18, fontWeight: 700, color: "#cbd5e1", marginBottom: 8 }}>No results found for &ldquo;{searchQuery}&rdquo;</p>
                    <p style={{ fontSize: 14, color: "#64748b", maxWidth: 400, margin: "0 auto" }}>
                      This doesn&apos;t appear to be a sports betting query. Try searching for a team, match, sport, bookmaker, or bet type.
                    </p>
                    <div style={{ marginTop: 20, display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" }}>
                      {["Lakers odds", "EPL matches", "DraftKings", "arbitrage cricket", "Best NBA value bets"].map(s => (
                        <button key={s} onClick={() => { setSearchQuery(s); runSearch(s); }}
                          style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)", color: "#60a5fa", padding: "6px 14px", borderRadius: 8, fontSize: 12, cursor: "pointer", fontWeight: 600 }}>
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Insight Card */}
                {searchResults.is_betting_related !== false && searchResults.ai_answer && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                    style={{
                      marginBottom: 24, padding: "16px 20px",
                      background: "linear-gradient(135deg, rgba(124,58,237,0.12), rgba(59,130,246,0.08))",
                      border: "1px solid rgba(124,58,237,0.25)",
                      borderRadius: 14,
                      display: "flex", alignItems: "flex-start", gap: 14,
                    }}
                  >
                    <div style={{ fontSize: 28, lineHeight: 1, flexShrink: 0 }}>🤖</div>
                    <div>
                      <p style={{ fontSize: 11, color: "#a78bfa", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>BetSmart AI Insight</p>
                      <p style={{ fontSize: 14, color: "#cbd5e1", lineHeight: 1.65 }}>{searchResults.ai_answer}</p>
                    </div>
                  </motion.div>
                )}

                {/* No match data found but is betting-related */}
                {searchResults.is_betting_related !== false &&
                  searchResults.matches.length === 0 && searchResults.sites.length === 0 && searchResults.genres.length === 0 && !searchLoading && (
                    <div style={{ padding: "32px", textAlign: "center", color: "#64748b", fontSize: 14 }}>
                      No specific matches or bookmakers found for &ldquo;{searchQuery}&rdquo;.
                      Try a team name like &ldquo;Lakers&rdquo;, &ldquo;Real Madrid&rdquo;, or a sport like &ldquo;NBA&rdquo;.
                    </div>
                  )}

                <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>

                  {/* --- Matches --- */}
                  {searchResults.matches.length > 0 && (
                    <div>
                      <p className="section-label" style={{ marginBottom: 12 }}>
                        🏟️  LIVE &amp; UPCOMING MATCHES
                      </p>
                      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {searchResults.matches.map((r, i) => (
                          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                            className={`glass ${r.analysis?.decision === "STRONG BET" ? "glass-green" : ""}`}
                            style={{ padding: 24 }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16, gap: 12, flexWrap: "wrap" }}>
                              <div>
                                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                                  <span className="badge-live"><span className="live-dot" /> LIVE</span>
                                  <p style={{ fontSize: 11, color: "var(--neon-blue)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700 }}>{r.genre}</p>
                                </div>
                                <h3 style={{ fontSize: 20, fontWeight: 800, color: "var(--text-primary)", fontFamily: "Inter, sans-serif" }}>{r.match}</h3>
                              </div>
                              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                                {r.analysis?.math?.ev > 2 && (
                                  <span className="badge-value" style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                                    +{r.analysis.math.ev.toFixed(1)}% EV
                                  </span>
                                )}
                                {r.analysis && <DecisionBadge d={r.analysis.decision} />}
                              </div>
                            </div>

                            <hr className="cyber-divider" />

                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12, marginTop: 16 }}>
                              {r.best_odds.map((o: any, j: number) => (
                                <div key={j} style={{
                                  background: "rgba(13,22,40,0.4)",
                                  padding: "16px",
                                  borderRadius: 12,
                                  border: "1px solid rgba(0,212,255,0.06)",
                                  transition: "border-color 0.2s",
                                }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                                    <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-secondary)", letterSpacing: "0.02em" }}>{o.outcome}</span>
                                    <span className="odds-pill">{o.odds}</span>
                                  </div>
                                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                      <span style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600 }}>{o.book}</span>
                                      {o.region_locked && (
                                        <span style={{ fontSize: 9, background: "rgba(255,77,109,0.1)", color: "var(--neon-red)", padding: "2px 6px", borderRadius: 4, fontWeight: 800, border: "1px solid rgba(255,77,109,0.2)" }}>🔒 US ONLY</span>
                                      )}
                                    </div>
                                    <a href={o.link} target="_blank" rel="noopener noreferrer" className="bet-now-btn">
                                      BET NOW →
                                    </a>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* --- Recommended Bookmakers --- */}
                  {searchResults.sites.length > 0 && (
                    <div>
                      <p style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12, fontWeight: 700 }}>🏦  Specialist Bookmakers</p>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
                        {searchResults.sites.map((site, i) => (
                          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                            className="glass" style={{ padding: 20, borderLeft: "4px solid #f5b942", display: "flex", flexDirection: "column", gap: 12 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <h4 style={{ fontWeight: 800, color: "#fff", fontSize: 16 }}>{site.name}</h4>
                              <span style={{ fontSize: 10, background: "rgba(6,78,59,0.4)", color: "#6ee7b7", padding: "3px 8px", borderRadius: 6, fontWeight: 700, border: "1px solid rgba(110,231,183,0.15)" }}>
                                🎁 Bonus
                              </span>
                            </div>
                            <p style={{ fontSize: 12, color: "#6ee7b7", background: "rgba(16,185,129,0.07)", padding: "6px 10px", borderRadius: 7, fontWeight: 600 }}>{site.bonus}</p>
                            <p style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.6 }}>{site.reason}</p>
                            {site.pro_tip && (
                              <p style={{ fontSize: 12, color: "#fbbf24", background: "rgba(251,191,36,0.06)", padding: "8px 12px", borderRadius: 8, borderLeft: "3px solid rgba(251,191,36,0.35)", lineHeight: 1.6 }}>
                                💡 <strong>Pro tip:</strong> {site.pro_tip}
                              </p>
                            )}
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "auto" }}>
                              <span style={{ fontSize: 10, color: "#475569" }}>Best for: {site.genre_context}</span>
                              <a href={site.url} target="_blank" rel="noopener noreferrer"
                                style={{ fontSize: 12, color: "#f5b942", fontWeight: 700, textDecoration: "none", padding: "6px 14px", background: "rgba(245,185,66,0.1)", border: "1px solid rgba(245,185,66,0.25)", borderRadius: 8 }}
                              >Visit Site →</a>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* --- Related Genres --- */}
                  {searchResults.genres.length > 0 && (
                    <div>
                      <p style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12, fontWeight: 700 }}>🎯  Related Sports &amp; Markets</p>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
                        {searchResults.genres.map((g, i) => (
                          <motion.div key={i} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
                            className="glass" style={{ padding: "14px 22px", borderRadius: 14, display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}
                            onClick={() => { setSearchQuery(g.name); runSearch(g.name); }}
                          >
                            <span style={{ fontSize: 26 }}>{g.icon}</span>
                            <div>
                              <p style={{ fontWeight: 700, color: "#fff", fontSize: 14 }}>{g.name}</p>
                              <p style={{ fontSize: 11, color: "#64748b" }}>Top {g.best_sites?.length || 0} bookmakers</p>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  )}

                </div>
              </section>
            )}

            {/* Arbitrage */}
            <section>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: "var(--neon-gold)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8, fontFamily: "Inter, sans-serif" }}>
                💰 ARBITRAGE OPPORTUNITIES
              </h2>
              {data.arbitrage?.length > 0 ? (
                data.arbitrage.map((a: any, i: number) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}
                    className="glass glass-green" style={{ padding: 20, marginBottom: 16 }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10, gap: 8 }}>
                      <p style={{ fontWeight: 800, fontSize: 18, color: "var(--text-primary)" }}>{a.match}</p>
                      <span className="badge-value" style={{ fontSize: 14 }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ display: "inline", marginRight: 4, verticalAlign: "-2px" }}><line x1="12" y1="2" x2="12" y2="22"></line><polyline points="17 5 12 2 7 5"></polyline></svg>
                        +{a.arb_margin}% RETURN
                      </span>
                    </div>
                    <hr className="cyber-divider" style={{ marginBottom: 12 }} />
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                      {a.bets.map((b: any, j: number) => (
                        <div key={j} style={{
                          background: "rgba(13,22,40,0.5)",
                          padding: "16px",
                          borderRadius: 12,
                          display: "flex",
                          flexDirection: "column",
                          gap: 10,
                          border: "1px solid rgba(0,255,136,0.15)",
                          position: "relative",
                          overflow: "hidden"
                        }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{b.outcome}</span>
                            <span className="odds-pill">@ {b.odds}</span>
                          </div>

                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                            <div>
                              <p className="section-label" style={{ marginBottom: 2 }}>RECOMMENDED STAKE</p>
                              <p style={{ fontWeight: 800, color: "var(--neon-green)", fontSize: 20, fontFamily: "Rajdhani, monospace" }}>₹{b.stake}</p>
                            </div>
                            <div style={{ textAlign: "right" }}>
                              <p style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 600, marginBottom: 4 }}>{b.book}</p>
                              <a
                                href={b.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="bet-now-btn"
                              >
                                EXECUTE BET →
                              </a>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ))
              ) : (
                <p className="glass" style={{ color: "#64748b", fontStyle: "italic", padding: 16, fontSize: 14 }}>
                  No arbitrage opportunities right now. Markets are efficient.
                </p>
              )}
            </section>

            {/* AI Decisions */}
            <section>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: "var(--neon-blue)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                📈 AI Betting Decisions
              </h2>

              {/* Group decisions by genre */}
              {Object.entries(
                data.decisions.reduce((acc: any, d: any) => {
                  const g = d.genre || "Other";
                  if (!acc[g]) acc[g] = [];
                  acc[g].push(d);
                  return acc;
                }, {})
              ).map(([genre, decisions]: [string, any]) => (
                <div key={genre} style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 800, color: "var(--text-primary)", marginBottom: 12, borderBottom: "1px solid var(--border-subtle)", paddingBottom: 6, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                    › {genre}
                  </h3>
                  {decisions.map((d: any, i: number) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                      className="glass" style={{ padding: 20, marginBottom: 10 }}
                    >
                      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                        <div>
                          <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>{d.match}</p>
                          <p style={{ color: "var(--neon-gold)", fontSize: 13, marginTop: 2 }}>{d.outcome}</p>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                          <span className="odds-pill" style={{ fontSize: 16 }}>
                            {d.odds}
                          </span>
                          <DecisionBadge d={d.analysis.decision} />
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 10, marginTop: 12, fontSize: 12 }}>
                        {[["EV", `${d.analysis.math.ev}%`], ["Edge", d.analysis.math.edge], ["Kelly", d.analysis.math.kelly]].map(([k, v]) => (
                          <span key={k} style={{ background: "rgba(0,212,255,0.08)", border: "1px solid rgba(0,212,255,0.15)", padding: "4px 8px", borderRadius: 6, color: "var(--text-primary)", fontWeight: 600 }}>
                            <span className="section-label" style={{ color: "var(--neon-blue)", marginRight: 4 }}>{k}:</span> {v}
                          </span>
                        ))}
                      </div>
                      <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 12, borderLeft: "2px solid rgba(0,212,255,0.4)", paddingLeft: 12, lineHeight: 1.6 }}>
                        {d.analysis.ai_explanation}
                      </p>
                    </motion.div>
                  ))}
                </div>
              ))}
            </section>

            {/* Sports by Genre */}
            <section>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: "#c084fc", marginBottom: 4, display: "flex", alignItems: "center", gap: 8 }}>
                🌐 Sports by Genre — Best Betting Sites
              </h2>
              <p style={{ color: "#475569", fontSize: 13, marginBottom: 16 }}>
                Expand a genre to see the best bookmakers for each sport and expert pro tips to maximise your edge.
              </p>
              {genresLoading
                ? <div style={{ color: "#475569", textAlign: "center", padding: 32 }} className="animate-pulse">Loading genres…</div>
                : <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {genres.map(g => <GenreCard key={g.genre} genre={g} />)}
                </div>
              }
            </section>
          </div>
        )}

        {/* ══════════════════════════════════════════════════
            CASINO TAB
        ══════════════════════════════════════════════════ */}
        {tab === "casino" && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: 36 }}>

            {/* ── BLACKJACK ──────────────────────────── */}
            <section className="glass" style={{ padding: 28 }}>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: "#4ade80", marginBottom: 4, display: "flex", alignItems: "center", gap: 8 }}>
                🃏 Blackjack Advisor
              </h2>
              <p style={{ color: "#475569", fontSize: 13, marginBottom: 20 }}>
                Pick your cards and the dealer's up-card. Advisor uses perfect basic strategy.
              </p>

              {/* Mode switcher */}
              <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
                {(["player", "dealer"] as const).map(m => (
                  <button key={m} onClick={() => setBjMode(m)}
                    style={{
                      padding: "9px 18px", borderRadius: 10, fontSize: 13, fontWeight: 700,
                      border: "none", cursor: "pointer", transition: "all 0.2s",
                      background: bjMode === m
                        ? (m === "player" ? "#16a34a" : "#dc2626")
                        : "rgba(255,255,255,0.04)",
                      color: bjMode === m ? "#fff" : "#94a3b8",
                    }}
                  >
                    {m === "player" ? "🟢 Add to Your Hand" : "🔴 Set Dealer Up-Card"}
                  </button>
                ))}
                <button
                  onClick={() => { setBjPlayerCards([]); setBjDealerCard(null); setBjResult(""); }}
                  style={{ marginLeft: "auto", padding: "9px 14px", borderRadius: 10, fontSize: 12, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8", cursor: "pointer" }}
                >
                  🗑 Clear
                </button>
              </div>

              {/* Current hands display */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
                {/* Player hand */}
                <div style={{
                  background: "rgba(34,197,94,0.04)", border: "1px solid rgba(34,197,94,0.2)",
                  borderRadius: 14, padding: 14,
                }}>
                  <p style={{ fontSize: 11, color: "#4ade80", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
                    Your Hand {bjPlayerCards.length > 0 && `— Total: ${bjTotal(bjPlayerCards)}`}
                  </p>
                  <div style={{ display: "flex", gap: 8, minHeight: 100, alignItems: "center", flexWrap: "wrap" }}>
                    {bjPlayerCards.length === 0 && <span style={{ color: "#374151", fontSize: 13 }}>Click cards below…</span>}
                    {bjPlayerCards.map((c, i) => (
                      <motion.div key={i} initial={{ scale: 0, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 350, damping: 22 }}>
                        <PlayingCard rank={c.rank} suit={c.suit} size="hand" variant="selected" onClick={() => handleBjCardClick(c.rank, c.suit)} />
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Dealer hand */}
                <div style={{
                  background: "rgba(255,77,109,0.04)", border: "1px solid rgba(255,77,109,0.2)",
                  borderRadius: 14, padding: 14,
                }}>
                  <p style={{ fontSize: 11, color: "var(--neon-red)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
                    Dealer Up-Card
                  </p>
                  <div style={{ display: "flex", gap: 8, minHeight: 100, alignItems: "center" }}>
                    {!bjDealerCard && <span style={{ color: "#374151", fontSize: 13 }}>Select dealer card…</span>}
                    {bjDealerCard && (
                      <>
                        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 350, damping: 22 }}>
                          <PlayingCard rank={bjDealerCard.rank} suit={bjDealerCard.suit} size="hand" variant="dealer"
                            onClick={() => { if (bjMode === "dealer") setBjDealerCard(null); }} />
                        </motion.div>
                        <CardBack size="hand" />
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Card picker */}
              <div style={{ marginBottom: 16 }}>
                <CardPickerGrid
                  mode="blackjack"
                  bjMode={bjMode}
                  bjPlayerCards={bjPlayerCards}
                  bjDealerCard={bjDealerCard}
                  onBjClick={handleBjCardClick}
                />
              </div>

              <button
                className="btn-green" style={{ width: "100%" }}
                disabled={bjPlayerCards.length < 2 || !bjDealerCard || bjLoading}
                onClick={runBlackjack}
              >
                {bjLoading ? "Analysing…" : "⚡ Get Strategy"}
              </button>

              <AnimatePresence>
                {bjResult && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                    style={{
                      marginTop: 16, padding: 20, borderRadius: 14, textAlign: "center",
                      background: "rgba(34,197,94,0.06)", border: "1px solid rgba(34,197,94,0.2)",
                    }}
                  >
                    <p style={{ fontSize: 11, color: "#64748b", marginBottom: 6 }}>Basic Strategy Says</p>
                    <p style={{ fontSize: 36, fontWeight: 900, color: "#4ade80", letterSpacing: "0.05em" }}>{bjResult}</p>
                    <p style={{ fontSize: 12, color: "#64748b", marginTop: 6 }}>
                      Player: {bjTotal(bjPlayerCards)} | Dealer shows: {bjDealerCard ? rankValue(bjDealerCard.rank) : "—"}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </section>

            {/* ── POKER v2 ───────────────────────────── */}
            <section className="glass" style={{ padding: 28 }}>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: "#60a5fa", marginBottom: 4, display: "flex", alignItems: "center", gap: 8 }}>
                ♠ Poker Advisor
              </h2>
              <p style={{ color: "#475569", fontSize: 13, marginBottom: 20 }}>
                Select your 2 hole cards and any community cards. Enter pot size, call amount, and opponent aggression for an accurate decision.
              </p>

              {/* Hole + Community display */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                <div style={{
                  background: "rgba(59,130,246,0.04)", border: "1px solid rgba(59,130,246,0.2)",
                  borderRadius: 14, padding: 14,
                }}>
                  <p style={{ fontSize: 11, color: "#60a5fa", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
                    Your Hole Cards ({holeSet.size}/2)
                  </p>
                  <div style={{ display: "flex", gap: 8, minHeight: 100, alignItems: "center" }}>
                    {holeSet.size === 0 && <span style={{ color: "#374151", fontSize: 13 }}>Click cards below…</span>}
                    {Array.from(holeSet).map(id => {
                      const { rank, suit } = cardFromId(id);
                      return (
                        <motion.div key={id} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 350, damping: 22 }}>
                          <PlayingCard rank={rank} suit={suit} size="hand" variant="selected" onClick={() => toggleHole(id)} />
                        </motion.div>
                      );
                    })}
                  </div>
                </div>

                <div style={{
                  background: "rgba(168,85,247,0.04)", border: "1px solid rgba(168,85,247,0.2)",
                  borderRadius: 14, padding: 14,
                }}>
                  <p style={{ fontSize: 11, color: "#c084fc", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
                    Community Cards ({communitySet.size}/5)
                  </p>
                  <div style={{ display: "flex", gap: 8, minHeight: 100, alignItems: "center", flexWrap: "wrap" }}>
                    {communitySet.size === 0 && <span style={{ color: "#374151", fontSize: 13 }}>Flop / Turn / River…</span>}
                    {Array.from(communitySet).map(id => {
                      const { rank, suit } = cardFromId(id);
                      return (
                        <motion.div key={id} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 350, damping: 22 }}>
                          <PlayingCard rank={rank} suit={suit} size="hand" variant="community" onClick={() => toggleCommunity(id)} />
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Card picker */}
              <div style={{ marginBottom: 20 }}>
                <CardPickerGrid
                  mode="poker"
                  holeSelected={holeSet}
                  communitySelected={communitySet}
                  maxHole={2} maxCommunity={5}
                  onHoleToggle={toggleHole}
                  onCommunityToggle={toggleCommunity}
                />
              </div>

              {/* Inputs — Pot, Call, Opponents */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                <div>
                  <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>Pot Size (₹)</label>
                  <input type="number" value={potSize} min={0}
                    onChange={e => setPotSize(Number(e.target.value))}
                    className="bs-input" placeholder="e.g. 500" />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>Call Amount (₹) — 0 to check</label>
                  <input type="number" value={callAmt} min={0}
                    onChange={e => setCallAmt(Number(e.target.value))}
                    className="bs-input" placeholder="e.g. 100" />
                </div>
              </div>

              {/* Opponent inputs — new section */}
              <div style={{
                background: "rgba(249,115,22,0.05)", border: "1px solid rgba(249,115,22,0.2)",
                borderRadius: 12, padding: 14, marginBottom: 20,
              }}>
                <p style={{ fontSize: 11, color: "#fb923c", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
                  👥 Opponent Info
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>
                      Opponents' Total Bet (₹) — all players combined
                    </label>
                    <input type="number" value={oppBet} min={0}
                      onChange={e => setOppBet(Number(e.target.value))}
                      className="bs-input" placeholder="e.g. 300" />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, color: "#94a3b8", display: "block", marginBottom: 4 }}>
                      Number of Active Opponents
                    </label>
                    <input type="number" value={numOpponents} min={1} max={9}
                      onChange={e => setNumOpponents(Number(e.target.value))}
                      className="bs-input" placeholder="e.g. 2" />
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", gap: 10 }}>
                <button className="btn-blue" style={{ flex: 1 }}
                  disabled={holeSet.size < 2 || pokerLoading}
                  onClick={runPoker}
                >
                  {pokerLoading ? "Analysing…" : "⚡ Calculate Best Move"}
                </button>
                <button
                  onClick={() => { setHoleSet(new Set()); setCommunitySet(new Set()); setPokerResult(null); setOppBet(0); }}
                  style={{ padding: "11px 16px", borderRadius: 10, fontSize: 13, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8", cursor: "pointer" }}
                >
                  🗑 Clear
                </button>
              </div>

              <AnimatePresence>
                {pokerResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                    style={{
                      marginTop: 20, borderRadius: 14, padding: 20,
                      background: "rgba(59,130,246,0.05)", border: "1px solid rgba(59,130,246,0.2)",
                      display: "flex", flexDirection: "column", gap: 14,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                      <div>
                        <p style={{ fontSize: 11, color: "#64748b" }}>{pokerResult.street}</p>
                        <p style={{ fontWeight: 800, color: "#e2e8f0", fontSize: 18 }}>{pokerResult.hand_name}</p>
                      </div>
                      <DecisionBadge d={pokerResult.decision} />
                    </div>

                    {/* Metrics grid */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 10 }}>
                      {[
                        ["Equity", `${pokerResult.equity}%`, "var(--neon-blue)"],
                        ["Pot Odds", `${pokerResult.pot_odds}%`, "var(--neon-gold)"],
                        ["Implied Odds", `${pokerResult.implied_odds}%`, "#fb923c"],
                        ["Edge", `${pokerResult.edge > 0 ? "+" : ""}${pokerResult.edge}%`, pokerResult.edge >= 0 ? "var(--neon-green)" : "var(--neon-red)"],
                      ].map(([label, val, color]) => (
                        <div key={label} style={{ background: "rgba(255,255,255,0.04)", borderRadius: 10, padding: "12px 8px", textAlign: "center", border: "1px solid rgba(255,255,255,0.05)" }}>
                          <p style={{ fontSize: 10, color: "var(--text-secondary)", marginBottom: 4, letterSpacing: "0.05em", textTransform: "uppercase", fontWeight: 700 }}>{label}</p>
                          <p style={{ fontWeight: 800, fontSize: 16, color: color as string, fontFamily: "Rajdhani, monospace" }}>{val}</p>
                        </div>
                      ))}
                    </div>

                    {/* Opponent pressure */}
                    {pokerResult.opponent_pressure && pokerResult.opponent_pressure !== "N/A" && (
                      <div style={{
                        padding: "10px 14px", borderRadius: 10,
                        background: "rgba(249,115,22,0.06)", border: "1px solid rgba(249,115,22,0.2)",
                        fontSize: 13, color: "#fdba74",
                      }}>
                        👥 {pokerResult.opponent_pressure}
                      </div>
                    )}

                    {/* Advice */}
                    <p style={{ fontSize: 14, color: "#cbd5e1", borderLeft: "3px solid rgba(59,130,246,0.5)", paddingLeft: 12, lineHeight: 1.65 }}>
                      {pokerResult.advice}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </section>
          </div>
        )}

        {/* ══════════════════════════════════════════════════
            STRATEGY / CHAT TAB
        ══════════════════════════════════════════════════ */}
        {tab === "strategy" && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)" }}>

            <div style={{ marginBottom: 16 }}>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: "var(--neon-purple)", display: "flex", alignItems: "center", gap: 8 }}>
                🧠 AI Betting Strategist
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 4 }}>
                Powered by Llama 3 70B via Groq. Ask anything about gambling — sports betting, poker, bankroll management, EV, casino strategy.
              </p>
            </div>

            {/* Chat messages area */}
            <div className="glass" style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 14, padding: "20px 16px", marginBottom: 16, minHeight: 0 }}>

              {chatHistory.length === 0 && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ textAlign: "center", padding: "40px 0" }}>
                  <div style={{ fontSize: 52, marginBottom: 12 }}>🧠</div>
                  <p style={{ color: "var(--text-primary)", fontSize: 16, fontWeight: 600 }}>Your AI Betting Strategist is ready.</p>
                  <p style={{ color: "var(--text-secondary)", fontSize: 13, marginTop: 6 }}>
                    Ask me anything about gambling strategy — I only discuss betting &amp; casino topics.
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 24 }}>
                    {STARTERS.map(s => (
                      <button key={s} onClick={() => sendChat(s)}
                        style={{
                          fontSize: 12, padding: "8px 14px", borderRadius: 999,
                          border: "1px solid rgba(192,132,252,0.3)",
                          color: "var(--neon-purple)", background: "rgba(192,132,252,0.05)",
                          cursor: "pointer", transition: "all 0.2s", textAlign: "left",
                        }}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </motion.div>
              )}

              {chatHistory.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.03 }}
                  style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", alignItems: "flex-end", gap: 8 }}
                >
                  {msg.role === "assistant" && (
                    <span style={{
                      width: 32, height: 32, borderRadius: "50%",
                      background: "rgba(168,85,247,0.15)", border: "1px solid rgba(168,85,247,0.3)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 14, flexShrink: 0,
                    }}>🧠</span>
                  )}
                  <div className={msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}>
                    {msg.content}
                  </div>
                </motion.div>
              ))}

              {chatLoading && (
                <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
                  <span style={{
                    width: 32, height: 32, borderRadius: "50%",
                    background: "rgba(168,85,247,0.15)", border: "1px solid rgba(168,85,247,0.3)",
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14,
                  }}>🧠</span>
                  <TypingIndicator />
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Quick chips (after first message) */}
            {chatHistory.length > 0 && chatHistory.length < 5 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                {STARTERS.slice(0, 4).map(s => (
                  <button key={s} onClick={() => sendChat(s)}
                    style={{
                      fontSize: 11, padding: "5px 12px", borderRadius: 999,
                      border: "1px solid rgba(100,116,139,0.3)", color: "#94a3b8",
                      background: "transparent", cursor: "pointer", transition: "all 0.2s",
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Input row */}
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") sendChat(); }}
                placeholder="Ask about poker, sports betting, blackjack strategy…"
                className="bs-input"
                style={{ flex: 1 }}
                disabled={chatLoading}
              />
              <button
                className="btn-primary"
                style={{ flexShrink: 0 }}
                disabled={!chatInput.trim() || chatLoading}
                onClick={() => sendChat()}
              >
                Send ↑
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}