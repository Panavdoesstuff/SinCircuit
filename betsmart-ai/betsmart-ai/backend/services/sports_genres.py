"""
Sports genre mapping with best betting sites per genre.
Each genre has a list of sports/leagues and recommended bookmakers
with reasons & bonuses to maximize the user's profit.
"""

SPORTS_GENRES = [
    {
        "genre": "Cricket",
        "icon": "🏏",
        "color": "#22c55e",
        "sports": [
            "IPL (Indian Premier League)",
            "Test Cricket",
            "T20 World Cup",
            "ODI Internationals",
            "The Ashes (Aus vs Eng)",
            "Big Bash League (BBL)",
            "Caribbean Premier League (CPL)",
            "SA20 League"
        ],
        "best_sites": [
            {
                "name": "Bet365",
                "url": "https://www.bet365.com",
                "reason": "Best-in-class cricket markets, live streaming for IPL and Test matches, deep ball-by-ball markets",
                "bonus": "Up to ₹10,000 welcome deposit bonus",
                "pro_tip": "Exploit live in-play odds swings after wickets — Bet365 is slowest to update, giving value windows"
            },
            {
                "name": "Betway",
                "url": "https://www.betway.com",
                "reason": "Fantastic IPL and T20 odds, fast payouts, top-wicket and over/under markets",
                "bonus": "100% match bonus up to ₹2,500",
                "pro_tip": "Betway regularly offers boosted odds on IPL finalists — check promotions before each match"
            },
            {
                "name": "10CRIC",
                "url": "https://www.10cric.com",
                "reason": "India-focused bookmaker with the widest IPL market range and INR deposits via UPI",
                "bonus": "150% first deposit bonus up to ₹20,000",
                "pro_tip": "10CRIC offers player-performance props not available elsewhere — great for top-scorer markets"
            },
            {
                "name": "Pure Win",
                "url": "https://www.purewin.com",
                "reason": "Excellent T20I odds, especially for India home matches. Competitive margins on Asian cricket",
                "bonus": "150% welcome bonus + weekly reload offers",
                "pro_tip": "Use Pure Win for live toss betting — they offer it earliest and with the best odds"
            }
        ]
    },
    {
        "genre": "Football / Soccer",
        "icon": "⚽",
        "color": "#3b82f6",
        "sports": [
            "English Premier League (EPL)",
            "La Liga (Spain)",
            "UEFA Champions League",
            "Bundesliga (Germany)",
            "Serie A (Italy)",
            "Ligue 1 (France)",
            "FIFA World Cup",
            "Euro Championship",
            "MLS (USA)",
            "J1 League (Japan)"
        ],
        "best_sites": [
            {
                "name": "Pinnacle",
                "url": "https://www.pinnacle.com",
                "reason": "Highest limits, lowest margins in the industry (~2-3% on EPL). The sharpest book alive",
                "bonus": "No traditional bonus — advantage is the odds themselves",
                "pro_tip": "Pinnacle accepts winners. Use their lines as the benchmark; any book offering better price = value"
            },
            {
                "name": "DraftKings Sportsbook",
                "url": "https://www.draftkings.com",
                "reason": "Excellent SGP (Same Game Parlay) builder for EPL/UCL, competitive boosts on big fixtures",
                "bonus": "Bet ₹5 get ₹200 in bonus bets",
                "pro_tip": "Build SGPs on DraftKings for big UCL nights — their correlations in parlays are favorable"
            },
            {
                "name": "Bet365",
                "url": "https://www.bet365.com",
                "reason": "Widest football market variety globally — 200+ markets per match, live streaming",
                "bonus": "Up to ₹10,000 welcome bonus",
                "pro_tip": "Bet365's Asian Handicap lines on La Liga are the sharpest — great for value bettors"
            },
            {
                "name": "Unibet",
                "url": "https://www.unibet.com",
                "reason": "Great Bundesliga and Serie A odds, strong cash-out feature for live matches",
                "bonus": "₹4,000 in free bet tokens",
                "pro_tip": "Unibet's early price offers on weekday fixtures (Tuesday/Wednesday) regularly beat the market"
            }
        ]
    },
    {
        "genre": "Basketball",
        "icon": "🏀",
        "color": "#f97316",
        "sports": [
            "NBA (National Basketball Association)",
            "EuroLeague",
            "NCAA March Madness",
            "FIBA Basketball World Cup",
            "NBL (Australia)",
            "G League",
            "Olympics Basketball"
        ],
        "best_sites": [
            {
                "name": "FanDuel Sportsbook",
                "url": "https://www.fanduel.com",
                "reason": "Best NBA player prop market. Deepest lines on points/rebounds/assists per game",
                "bonus": "Bet ₹5 win ₹150 in bonus bets (no odds requirement)",
                "pro_tip": "Exploit FanDuel's same-game parlay promos during NBA playoffs — they heavily subsidize these"
            },
            {
                "name": "DraftKings",
                "url": "https://www.draftkings.com",
                "reason": "Top NBA live betting platform, fast lines, boosted odds on featured games",
                "bonus": "20% deposit match up to ₹1,000",
                "pro_tip": "DraftKings posts NBA lines Tuesday for Sunday games — early lines have biggest edges"
            },
            {
                "name": "BetMGM",
                "url": "https://www.betmgm.com",
                "reason": "One Key loyalty program, strong EuroLeague coverage, competitive NBA spreads",
                "bonus": "First bet match up to ₹15,000",
                "pro_tip": "BetMGM lets you edit live bets — use this to lock profits on NBA blowouts in Q4"
            }
        ]
    },
    {
        "genre": "Tennis",
        "icon": "🎾",
        "color": "#facc15",
        "sports": [
            "Wimbledon",
            "US Open",
            "French Open (Roland Garros)",
            "Australian Open",
            "ATP Tour Masters 1000",
            "WTA Tour",
            "Davis Cup",
            "Laver Cup"
        ],
        "best_sites": [
            {
                "name": "Pinnacle",
                "url": "https://www.pinnacle.com",
                "reason": "Lowest margins on Grand Slams (~1.5%). Best place for pre-match tennis value",
                "bonus": "Advantage: best odds in the market",
                "pro_tip": "Surface specialists (clay experts at Roland Garros) are systematically underrated by books — bet them early"
            },
            {
                "name": "Bet365",
                "url": "https://www.bet365.com",
                "reason": "Live streaming of ATP/WTA events, deep in-play markets (set betting, game handicaps)",
                "bonus": "Up to ₹10,000 welcome bonus",
                "pro_tip": "Tennis in-play is gold after first set — Bet365 adjusts lines slowly on upset patterns. Exploit this"
            },
            {
                "name": "Betfair Exchange",
                "url": "https://www.betfair.com",
                "reason": "Bet against the bookmaker — you set the odds. Lowest effective vig in tennis on exchanges",
                "bonus": "No traditional bonus but 0% commission first month",
                "pro_tip": "Lay favorites at Betfair post-first-set when they've dropped — variance is high in tennis"
            }
        ]
    },
    {
        "genre": "American Football",
        "icon": "🏈",
        "color": "#a78bfa",
        "sports": [
            "NFL (National Football League)",
            "Super Bowl",
            "NFL Draft Props",
            "College Football (NCAAF)",
            "CFL (Canada)",
            "XFL"
        ],
        "best_sites": [
            {
                "name": "FanDuel Sportsbook",
                "url": "https://www.fanduel.com",
                "reason": "Best NFL player props market — touchdowns, receiving yards, passing yards all deeply priced",
                "bonus": "Bet ₹5 win ₹150 in bonus bets",
                "pro_tip": "FanDuel's no-sweat SGP promo (refund if SGP loses) during Sunday NFL is a must-use"
            },
            {
                "name": "DraftKings",
                "url": "https://www.draftkings.com",
                "reason": "Sharpest NFL spread lines in the US market, strong Monday Night Football promos",
                "bonus": "20% deposit match + step-up bonus",
                "pro_tip": "DraftKings posts next week's NFL lines on Monday nights. Early lines before public money moves = value"
            },
            {
                "name": "BetMGM",
                "url": "https://www.betmgm.com",
                "reason": "Unique 'Parlay Plus' boosted payouts on NFL, strong Super Bowl prop market",
                "bonus": "First bet match up to ₹15,000",
                "pro_tip": "BetMGM's touchdown scorer markets have sharp pricing on weekend games — pay attention to injury reports"
            }
        ]
    },
    {
        "genre": "Baseball",
        "icon": "⚾",
        "color": "#ef4444",
        "sports": [
            "MLB (Major League Baseball)",
            "World Series",
            "MLB Home Run Derby",
            "NPB (Japan Pro Baseball)",
            "KBO (Korean Baseball)",
            "College Baseball (NCAAB)"
        ],
        "best_sites": [
            {
                "name": "Pinnacle",
                "url": "https://www.pinnacle.com",
                "reason": "Sharpest MLB moneylines globally, accepts large stakes, no restrictions on winners",
                "bonus": "Advantage: lowest juice (-105/-105 on spreads vs -110/-110 elsewhere)",
                "pro_tip": "MLB run line (+1.5/-1.5) betting has strong closing line value opportunities — track line movement"
            },
            {
                "name": "BetOnline",
                "url": "https://www.betonline.ag",
                "reason": "Strong MLB markets, competitive NRFI (No Run First Inning) props",
                "bonus": "50% welcome bonus up to ₹25,000 in crypto",
                "pro_tip": "BetOnline's pitcher props (strikeouts, innings pitched) have weaker lines than player markets — target these"
            },
            {
                "name": "FanDuel",
                "url": "https://www.fanduel.com",
                "reason": "Deep MLB player props (hits, total bases, RBIs) and strong live betting",
                "bonus": "Bet ₹5 win ₹150 in bonus bets",
                "pro_tip": "Batter vs pitcher matchup props on FanDuel are often mispriced on lefty/righty splits"
            }
        ]
    },
    {
        "genre": "MMA & Boxing",
        "icon": "🥊",
        "color": "#f43f5e",
        "sports": [
            "UFC (Ultimate Fighting Championship)",
            "Bellator MMA",
            "ONE Championship",
            "Heavyweight World Boxing",
            "IBF / WBC / WBA / WBO Title Fights",
            "PFL (Professional Fighters League)"
        ],
        "best_sites": [
            {
                "name": "BetOnline",
                "url": "https://www.betonline.ag",
                "reason": "Best UFC moneylines, method-of-victory and round betting markets, fast prop posting",
                "bonus": "50% welcome bonus up to ₹25,000",
                "pro_tip": "Round betting (fight to go distance) in UFC heavy favorite fights is extremely profitable — books overprice short finishes"
            },
            {
                "name": "DraftKings",
                "url": "https://www.draftkings.com",
                "reason": "Early UFC lines at sharp prices, method-of-victory SGPs",
                "bonus": "20% deposit match",
                "pro_tip": "UFC significant strikes props (over/under) on DraftKings are often mispriced for grinding wrestlers"
            },
            {
                "name": "BetMGM",
                "url": "https://www.betmgm.com",
                "reason": "Strong boxing lines, quick payout after bouts, prop bets on knockdowns per round",
                "bonus": "First bet match up to ₹15,000",
                "pro_tip": "BetMGM boxing props (total punches, round reached) are loosely priced — study CompuBox data for edge"
            }
        ]
    },
    {
        "genre": "Horse Racing",
        "icon": "🏇",
        "color": "#10b981",
        "sports": [
            "Royal Ascot (UK)",
            "Kentucky Derby (USA)",
            "The Melbourne Cup (Australia)",
            "Cheltenham Festival (UK)",
            "Dubai World Cup",
            "Champions Day (UK)",
            "Grand National (UK)",
            "Indian Derby (India)"
        ],
        "best_sites": [
            {
                "name": "Betfair Exchange",
                "url": "https://www.betfair.com",
                "reason": "The world's largest betting exchange — you ARE the bookmaker. Best odds for horses, lay betting",
                "bonus": "0% commission for first 60 days",
                "pro_tip": "In-play horse racing on Betfair: price crashes after the stalls open — lay the leader mid-race for green book"
            },
            {
                "name": "William Hill",
                "url": "https://www.williamhill.com",
                "reason": "Best Best Odds Guaranteed (BOG) on UK racing, wide each-way market coverage",
                "bonus": "₹5,000 in free bets",
                "pro_tip": "William Hill's Best Odds Guarantee means take the morning price on Cheltenham entries — you always get SP if higher"
            },
            {
                "name": "Paddy Power",
                "url": "https://www.paddypower.com",
                "reason": "Aggressive money-back promotions, non-runner refunds, and boosted each-way terms on big festivals",
                "bonus": "Money back if your horse finishes 2nd — unique offer",
                "pro_tip": "Paddy Power refunds losing bets on handicap races at major festivals (Cheltenham, Royal Ascot). Always bet there first"
            }
        ]
    }
]
