import { useState, useEffect, useRef } from "react";

export function useStream() {
  const [messages, setMessages] = useState([]);
  const [done, setDone] = useState(false);
  const esRef = useRef(null);

  const startStream = (streamUrl) => {
    if (esRef.current) esRef.current.close();
    setMessages([]);
    setDone(false);

    const es = new EventSource(streamUrl);
    esRef.current = es;

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.error) { es.close(); setDone(true); return; }

      setMessages(prev => {
        const last = prev[prev.length - 1];
        // If it's a new agent, add a new entry to the array
        if (!last || last.agent !== data.agent) {
          return [...prev, { 
            agent: data.agent, 
            text: data.token, 
            done: data.final, 
            full_text: data.full_text || "" 
          }];
        }
        // If it's the same agent, append the token to their text
        return [...prev.slice(0, -1), { 
          ...last, 
          text: last.text + data.token, 
          done: data.final, 
          full_text: data.full_text || "" 
        }];
      });

      // Stop the stream once the Director finishes
      if (data.final && data.agent === "Pit Wall Director") {
        es.close();
        setDone(true);
      }
    };
  };

  useEffect(() => {
    return () => { if (esRef.current) esRef.current.close(); };
  }, []);

  return { messages, done, startStream };
}