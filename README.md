The landing page :- https://sin-circuit.vercel.app
Once you reach this, wait for 5s, and then scroll down, hover over lewis hamilton and the card for a surprise :) 

WORLD OF PITSTOP (This backend utilizes a robust Edge Compute architecture. Because our Multi-Agent RAG system generates local 
semantic embeddings via PyTorch and ChromaDB, the strict memory requirements exceed standard free-tier constraints. 
Rather than heavily limiting our AI model to fit inside a basic cloud container, we chose to host the heavy machine-learning 
load locally because we didn't want to compromise on our AI logic)

PitStop Intelligence: Multi-Agent F1 race Simulator

It is a highly advanced, multi-agent AI simulation platform built to replicate the high-stakes, data driven environment of a 
Formula 1 race. It utilizes a complex System Design architecture featuring RAG (Retrieval Augmented Generation), 
localized vector embeddings, and autonomous agent debate to provide real time strategic recommendations based on live telemetry.

The problem :- Modern Formula 1 racing generates gigabytes of live telemetry per second. Human strategists (the Pit Wall) often
struggle to instantly cross-reference live tyre degradation, weather algorithms, and historical race data to make split-second pit decisions. 
Not just this, there's so many people out there(F1 FANS :) ) who would want to learn more about F1, how the sport works, the strategies,
the numbers and EVERYTHING That goes behind it.

Solution :- An autonomous Multi-Agent AI system that ingests live, simulated telemetry,cross-references it with a localized Vector Database 
of F1 historical knowledge, and mathematically debates the best course of action in real-time. We used multiple agents, fine tuned 
and optimised them, and they make decisions autonomously.
But we didn't just build this to happen quietly in the background. By utilizing Server-Sent Events (SSE), we stream the 
multi-agent AI debate directly to the frontend character-by-character in real-time. The user watches the AI literally "think" and 
argue out loud as the race happens live on the dashboard.

Impact - Demonstrates the immense capability of Multi-Agent Systems in hyper-fast, high-pressure environments where the problem fits 
perfectly into modern AI workflows.

Models used - Employs Groq (Llama 3.3 70B Versatile base) for ultra-fast, structured JSON generation and logic.
Semantic Embeddings - Uses sentence-transformers/all-MiniLM-L6-v2 to natively generate mathematical semantic embeddings locally, 
eliminating external API latency. 
Optimized Architecture - The race_engineer.py mathematically compares the live telemetry state (e.g., "Lap 30, soft tyres, cold weather") 
against defined "Track Profiles" (like Las Vegas) using Cosine Similarity to assign an autonomous "Confidence Score" to its recommendations.
Fine Tuning and prompt engineering - Fine tuned all the models like weather agent, tyre agent, race_engineer, and they do their job to 
perfection.

Design: multi-step reasoning pipelines - The system utilizes a structured, adversarial pipeline:
  1. Race Engineer (Agent A): Analyzes telemetry and battery (ERS) usage.
  2. Strategy Oracle (Agent B): Analyzes tyre cliff degradation physics and gap to the leader.
  3. Debate Orchestrator (Agent C): Forces the two agents into an autonomous debate over internal memory, mediates conflicts in their logic,
   and produces a final, unified JSON verdict.
Retrieval-Augmented Generation (RAG): Integrates ChromaDB as a completely local vector database. The knowledge_base.py and
retriever.py pipelines retrieve the top historical matches for immediate injection into the LLM context windows, giving the agents
"memories" of past races.

- agents: Contains isolated agent logic and internal system prompts.
- rag: Handles vector storage processing, embedding generation, and ChromaDB instantiation.
- simulation: A deterministic math engine controlling tyre wear mechanics, lap times, and dirty air physics completely
   independent of the AI layer.
- main.py: A cleanly structured FastAPI router handling WebSocket connections and Server-Sent Events (SSE).

 Deployed live and globally accessible on Vercel.

 Secure Flow: Environment variables are utilized securely via .env 

WORLD OF BETSMART AI
We deployed both thebackend and frontend. Simply go to the landing page at https://sin-circuit.vercel.app, and click on enter betsmart.

BETSMART AI : Gives you guaranteed(yes 100%) profit bets(mathematically it is a concept called arbitrage), and gives you suggestions 
              for blackjack and poker bettings, and sports odds, topped with a chatbot which specialises in strategy for gambling.

BetSmart AI is a high-performance intelligence platform. It combinesreal-time market data from The Odds API with a sophisticated 
Multi-Agent AI Orchestration layer. Rather than static tracking, BetSmart AI utilizes in depth mathematical analysis to debate and 
verify every betting recommendation.

The problem : Gambling/Betting a lot of money with no guarantee on return can potentially ruin someone's life savings.
              Moreover, there's opportunities in the betting market which nobody talks about, and is guaranteed money(arbitrage).

The solution : Let me first explain arbitrage. Let's take 2023 wc final bw india and aus. On indian platforms the odds of india winning
               were higher(1.45),and on stake, it was aus(3.50) which was higher. If a person put 7,7070 on indian platforms and 2,930
               on stake, the profit would be guaranteed, irrespective of the result, and would be 2.5 percent.
               Our betsmart AI does this by using API from oddsapi, and it scans the odds from all betting websites and gives us 
               opportunities where we can make guaranteed money(0-10% using arbitrage). It also has a sports section, where it 
               analyses odds and suggests if you should bet or not.
               Moreover, theres a blackjack and poker section where you can give it any scenario and it analyses it, and gives you 
               the mathematically best move possilbe.
               We have chatbot which is fine tuned(to talk only about betting) so no API calls are wasted, and you can ask it any 
               question, strategy and it answers it in detail.
               We have a search bar where you can search for current games to look to bet on them.

System Architecture

1.Multi-Agent Orchestration - The core analysis pipeline utilizes a structured, adversarial reasoning process involving three 
autonomous agents:

ScoutAgent (The Data Miner): Scans 50+ global bookmakers (US, UK, EU, AU) in real-time to detect raw market mispricing.

AnalystAgent (The Mathematician): Executes RAG-based analysis, cross-referencing live odds against historical data stored in a localized 
                                  vector database to identify "True Value."

CriticAgent (The Risk Manager): Mediates conflicts between agents, enforces strict Kelly Criterion bankroll management, a
                                and outputs a final unified JSON verdict.

2. Retrieval-Augmented Generation (RAG) & Embeddings 
To ensure our agents have "memory" of market trends, we implemented a full RAG pipeline:
Local Vector Database: We utilized ChromaDB  for localized storage of historical betting patterns and track profiles.
Semantic Understanding: We integrated sentence-transformers/all-MiniLM-L6-v2 to generate mathematical embeddings locally,      
                        assigned via Cosine Similarity to ensure ultra-low latency.

3. Real-Time Streaming AI Responses - By utilizing Server-Sent Events (SSE), we stream the multi-agent debate directly to the
                                     frontend character-by-character. This allows the user to watch the AI literally "think" and
                                     argue through its logic.

AI Engine: Groq (Llama 3 70B)  for high-speed logic and structured output.

Backend: Python (FastAPI)  for handling high-concurrency requests and SSE streaming.
Frontend: Next.js 16  with a custom "Obsidian" design system.

/agents: Isolated logic for the Scout, Analyst, and Critic including custom system prompts.
/rag: Vector storage processing and ChromaDB instantiation.
/services: Core business logic including Arbitrage Discovery and Casino Strategy engines.
/utils: Deterministic math engines for EV calculation and probability simulation.
main.py: Clean FastAPI entry point with structured pipeline management.

Security: All API keys (Groq, Odds API) are strictly managed via Environment Variables (.env). Secrets are never hardcoded or exposed in the frontend code

Deployment Integrity: The system is live and globally accessible, optimized for low-latency performance.

Every AI verdict includes a "Mathematical Analysis" field to explain the decision-making process to the user.
