import React, { useState, useEffect } from 'react';
import AgentDebate from './components/AgentDebate';
import TrackMap from './components/TrackMap';
import PitTimeline from './components/PitTimeline';
import TireVisual from './components/TireVisual';

const API_BASE = "http://localhost:8000";

export default function App() {
  const [raceId, setRaceId] = useState(null);
  const [state, setState] = useState(null);
  const [selectedStartTire, setSelectedStartTire] = useState('Medium');
  const [isStarted, setIsStarted] = useState(false);
  const [usedCompounds, setUsedCompounds] = useState([]); // Tracks rule compliance

  const startRace = async () => {
    const res = await fetch(`${API_BASE}/race/start`, { method: 'POST' });
    const data = await res.json();
    setRaceId(data.race_id);
    
    const pitRes = await fetch(`${API_BASE}/race/${data.race_id}/pit?compound=${selectedStartTire}`, { 
      method: 'POST' 
    });
    const pitData = await pitRes.json();
    
    setState(pitData.state);
    setUsedCompounds([selectedStartTire]); // Record first compound
    setIsStarted(true);
  };

  const handleTick = async () => {
    if (state.lap >= state.total_laps) return;
    const res = await fetch(`${API_BASE}/race/${raceId}/tick`, { method: 'POST' });
    const data = await res.json();
    setState(data.state); 
  };

  const handlePitStop = async (newCompound) => {
    try {
      const res = await fetch(`${API_BASE}/race/${raceId}/pit?compound=${newCompound}`, { 
        method: 'POST' 
      });
      const data = await res.json();
      setState(data.state);
      
      // Update our compliance list
      if (!usedCompounds.includes(newCompound)) {
        setUsedCompounds([...usedCompounds, newCompound]);
      }
    } catch (err) {
      console.error("Pit stop failed:", err);
    }
  };

  if (!isStarted) {
    return (
      <div style={{ backgroundColor: '#0b0b0b', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#fff', fontFamily: 'sans-serif' }}>
        <div style={{ textAlign: 'center', border: '1px solid #333', padding: '40px', borderRadius: '20px', background: '#151515' }}>
          <h1 style={{ color: '#e10600', marginBottom: '30px' }}>SIN CIRCUIT <span style={{color:'#fff'}}>STRATEGY</span></h1>
          <p style={{ color: '#888' }}>SELECT STARTING COMPOUND</p>
          <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', marginBottom: '30px' }}>
            {['Soft', 'Medium', 'Hard'].map(t => (
              <button key={t} onClick={() => setSelectedStartTire(t)}
                style={{
                  padding: '15px 25px', borderRadius: '8px', border: selectedStartTire === t ? '2px solid #e10600' : '1px solid #444',
                  background: selectedStartTire === t ? '#e1060022' : '#222', color: '#fff', cursor: 'pointer', fontWeight: 'bold'
                }}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>
          <button onClick={startRace} style={{ width: '100%', padding: '15px', background: '#e10600', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '18px', cursor: 'pointer' }}>
            START GRAND PRIX
          </button>
        </div>
      </div>
    );
  }

  const isRaceOver = state.lap >= state.total_laps;
  const hasMetRule = usedCompounds.length >= 2;

  return (
    <div style={{ backgroundColor: '#0b0b0b', minHeight: '100vh', color: '#fff', padding: '20px', fontFamily: 'sans-serif' }}>
      
      <div style={{ borderBottom: '2px solid #e10600', paddingBottom: '15px', marginBottom: '25px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: '28px' }}>SIN CIRCUIT <span style={{ color: '#e10600' }}>{isRaceOver ? '🏁 FINISHED' : 'AI ENGINE'}</span></h1>
        
        {/* RULE STATUS COMPONENT */}
        <div style={{ background: hasMetRule ? '#00ff0022' : '#ff990022', padding: '5px 15px', borderRadius: '20px', border: `1px solid ${hasMetRule ? '#00ff00' : '#ff9900'}`, fontSize: '11px', color: hasMetRule ? '#00ff00' : '#ff9900', fontWeight: 'bold' }}>
          {hasMetRule ? '✓ TYRE RULE MET' : '⚠ TWO COMPOUNDS REQUIRED'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 450px', gap: '25px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '25px' }}>
            <TrackMap currentLap={state.lap} totalLaps={state.total_laps} />
            <TireVisual compound={state.compound} age={state.tyre_age} />
          </div>
          
          <PitTimeline pitHistory={state.pit_history} currentLap={state.lap} compound={state.compound} />

          <div style={{ background: '#1a1a1a', padding: '20px', borderRadius: '12px', border: '1px solid #333' }}>
             <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={handleTick} disabled={isRaceOver} style={{ flex: 2, padding: '15px', background: isRaceOver ? '#333' : '#e10600', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
                {isRaceOver ? "CHECKERED FLAG" : "NEXT LAP →"}
              </button>
              <button onClick={() => handlePitStop('Soft')} style={{ flex: 1, padding: '15px', background: '#333', color: '#ff4d4d', border: '1px solid #ff4d4d', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>SOFT</button>
              <button onClick={() => handlePitStop('Medium')} style={{ flex: 1, padding: '15px', background: '#333', color: '#EF9F27', border: '1px solid #EF9F27', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>MED</button>
              <button onClick={() => handlePitStop('Hard')} style={{ flex: 1, padding: '15px', background: '#333', color: '#fff', border: '1px solid #fff', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>HARD</button>
            </div>
          </div>
        </div>

        <div style={{ background: '#151515', borderRadius: '16px', border: '1px solid #333', minHeight: '600px' }}>
          <AgentDebate raceId={raceId} apiBase={API_BASE} />
        </div>
      </div>
    </div>
  );
}