import { LineChart, Line, XAxis, YAxis,
         CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function LapChart({ lapData }) {
  // lapData: [{lap: 1, delta: 0.0}, {lap: 2, delta: 0.2}, ...]
  return (
    <div style={{padding:"1rem"}}>
      <div style={{fontSize:"11px",fontWeight:500,
                    textTransform:"uppercase",letterSpacing:"0.06em",
                    color:"#888",marginBottom:"8px"}}>
        Lap time delta to leader
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={lapData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee"/>
          <XAxis dataKey="lap" tick={{fontSize:11}}/>
          <YAxis tick={{fontSize:11}}/>
          <Tooltip/>
          <Line type="monotone" dataKey="delta"
                stroke="#E24B4A" strokeWidth={2} dot={false}/>
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}