import { useEffect, useRef, useState, useCallback } from 'react';

interface KiteState {
  x: number;
  y: number;
  vx: number;
  vy: number;
  angle: number;
  angularVelocity: number;
  altitude: number;
  stringLength: number;
  tension: number;
}

interface WindState {
  baseSpeed: number;
  gustStrength: number;
  gustPhase: number;
  direction: number;
}

interface TailNode {
  x: number;
  y: number;
}

const GRAVITY = 0.15;
const DRAG = 0.98;
const LIFT_COEFFICIENT = 0.08;
const STRING_STIFFNESS = 0.003;
const MAX_STRING_LENGTH = 800;
const MIN_STRING_LENGTH = 100;
const TAIL_LENGTH = 15;
const TAIL_SPACING = 8;

export function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const kiteRef = useRef<KiteState>({
    x: 400,
    y: 300,
    vx: 0,
    vy: 0,
    angle: -Math.PI / 4,
    angularVelocity: 0,
    altitude: 0,
    stringLength: 300,
    tension: 0,
  });
  const windRef = useRef<WindState>({
    baseSpeed: 2,
    gustStrength: 1,
    gustPhase: 0,
    direction: 0,
  });
  const tailRef = useRef<TailNode[]>([]);
  const keysRef = useRef<Set<string>>(new Set());
  const [altitude, setAltitude] = useState(0);
  const [tension, setTension] = useState(0);
  const [windSpeed, setWindSpeed] = useState(0);
  const [isTrickMode, setIsTrickMode] = useState(false);
  const [trickName, setTrickName] = useState('');
  const trickTimerRef = useRef<number | null>(null);

  const initTail = useCallback((startX?: number, startY?: number) => {
    const tail: TailNode[] = [];
    const x = startX ?? 400;
    const y = startY ?? 300;
    for (let i = 0; i < TAIL_LENGTH; i++) {
      tail.push({ x, y: y + i * TAIL_SPACING });
    }
    tailRef.current = tail;
  }, []);

  const updateWind = useCallback(() => {
    const wind = windRef.current;
    wind.gustPhase += 0.02;
    const gust = Math.sin(wind.gustPhase) * wind.gustStrength + 
                 Math.sin(wind.gustPhase * 2.3) * wind.gustStrength * 0.5;
    const currentWindSpeed = wind.baseSpeed + gust;
    setWindSpeed(currentWindSpeed);
    return currentWindSpeed;
  }, []);

  const updateTail = useCallback((kiteX: number, kiteY: number, kiteAngle: number) => {
    const tail = tailRef.current;
    const tailStartX = kiteX - Math.sin(kiteAngle) * 30;
    const tailStartY = kiteY + Math.cos(kiteAngle) * 30;

    // First node follows kite
    tail[0].x += (tailStartX - tail[0].x) * 0.3;
    tail[0].y += (tailStartY - tail[0].y) * 0.3;

    // Rest follow previous node with physics
    for (let i = 1; i < tail.length; i++) {
      const prev = tail[i - 1];
      const curr = tail[i];
      const dx = prev.x - curr.x;
      const dy = prev.y - curr.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const targetDist = TAIL_SPACING;

      if (dist > 0) {
        const force = (dist - targetDist) * 0.1;
        curr.x += (dx / dist) * force;
        curr.y += (dy / dist) * force;
      }

      // Add some wave motion
      curr.x += Math.sin(Date.now() * 0.005 + i * 0.5) * 0.5;
      
      // Gravity effect on tail
      curr.y += 0.5;
    }
  }, []);

  const performTrick = useCallback((trickType: string) => {
    const kite = kiteRef.current;
    setIsTrickMode(true);
    
    switch (trickType) {
      case 'loop':
        kite.angularVelocity = 0.3;
        setTrickName('Loop!');
        break;
      case 'dive':
        kite.vy = 8;
        kite.vx = 2;
        setTrickName('Power Dive!');
        break;
      case 'figure8':
        kite.vx = Math.sin(Date.now() * 0.01) * 5;
        setTrickName('Figure 8!');
        break;
    }

    if (trickTimerRef.current) {
      clearTimeout(trickTimerRef.current);
    }
    trickTimerRef.current = window.setTimeout(() => {
      setIsTrickMode(false);
      setTrickName('');
    }, 2000);
  }, []);

  const updatePhysics = useCallback(() => {
    const kite = kiteRef.current;
    const wind = updateWind();
    const keys = keysRef.current;

    // Calculate relative wind velocity
    const relativeWindX = wind - kite.vx;
    const relativeWindY = -kite.vy;

    // Lift force (perpendicular to kite surface)
    const angleOfAttack = kite.angle - Math.atan2(relativeWindY, relativeWindX);
    const lift = Math.sin(angleOfAttack) * LIFT_COEFFICIENT * Math.abs(relativeWindX);
    
    // Apply forces
    kite.vx += Math.cos(kite.angle) * lift;
    kite.vy += Math.sin(kite.angle) * lift - GRAVITY;

    // Wind drag
    kite.vx += relativeWindX * 0.001;
    kite.vy += relativeWindY * 0.001;

    // String constraint
    const anchorX = 400;
    const anchorY = 550;
    const dx = kite.x - anchorX;
    const dy = kite.y - anchorY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    
    if (dist > kite.stringLength) {
      const excess = dist - kite.stringLength;
      const tension = excess * STRING_STIFFNESS;
      kite.tension = tension;
      
      const nx = dx / dist;
      const ny = dy / dist;
      
      kite.vx -= nx * tension;
      kite.vy -= ny * tension;
      
      kite.x = anchorX + nx * kite.stringLength;
      kite.y = anchorY + ny * kite.stringLength;
    } else {
      kite.tension = 0;
    }

    // Apply drag
    kite.vx *= DRAG;
    kite.vy *= DRAG;

    // Update position
    kite.x += kite.vx;
    kite.y += kite.vy;

    // Update angle based on velocity and control
    const targetAngle = Math.atan2(kite.vy, kite.vx) + Math.PI / 2;
    const angleDiff = targetAngle - kite.angle;
    kite.angularVelocity += angleDiff * 0.01;
    kite.angularVelocity *= 0.95;
    kite.angle += kite.angularVelocity;

    // Control inputs
    if (keys.has('ArrowLeft')) {
      kite.vx -= 0.3;
      kite.angle -= 0.05;
    }
    if (keys.has('ArrowRight')) {
      kite.vx += 0.3;
      kite.angle += 0.05;
    }
    if (keys.has('ArrowUp')) {
      kite.vy -= 0.3;
    }
    if (keys.has('ArrowDown')) {
      kite.vy += 0.2;
    }

    // String length control
    if (keys.has('w') || keys.has('W')) {
      kite.stringLength = Math.min(kite.stringLength + 2, MAX_STRING_LENGTH);
    }
    if (keys.has('s') || keys.has('S')) {
      kite.stringLength = Math.max(kite.stringLength - 2, MIN_STRING_LENGTH);
    }

    // Calculate altitude (inverted Y, scaled)
    kite.altitude = Math.max(0, Math.round((550 - kite.y) / 10));
    setAltitude(kite.altitude);
    setTension(Math.round(kite.tension * 100));

    // Update tail
    updateTail(kite.x, kite.y, kite.angle);
  }, [updateWind, updateTail]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, '#87CEEB');
    gradient.addColorStop(0.5, '#B0E0E6');
    gradient.addColorStop(1, '#E0F6FF');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw clouds
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    for (let i = 0; i < 5; i++) {
      const x = (i * 200 + Date.now() * 0.02) % (canvas.width + 100) - 50;
      const y = 50 + i * 30;
      ctx.beginPath();
      ctx.arc(x, y, 30, 0, Math.PI * 2);
      ctx.arc(x + 25, y - 10, 35, 0, Math.PI * 2);
      ctx.arc(x + 50, y, 30, 0, Math.PI * 2);
      ctx.fill();
    }

    const kite = kiteRef.current;
    const anchorX = 400;
    const anchorY = 550;

    // Draw string
    ctx.strokeStyle = isTrickMode ? '#FF6B6B' : '#333';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(anchorX, anchorY);
    
    // Draw string with slight curve
    const midX = (anchorX + kite.x) / 2;
    const midY = (anchorY + kite.y) / 2;
    const sag = kite.tension * 2;
    ctx.quadraticCurveTo(midX, midY + sag, kite.x, kite.y);
    ctx.stroke();

    // Draw tail
    const tail = tailRef.current;
    ctx.strokeStyle = '#FF6B6B';
    ctx.lineWidth = 3;
    ctx.beginPath();
    if (tail.length > 0) {
      ctx.moveTo(tail[0].x, tail[0].y);
      for (let i = 1; i < tail.length; i++) {
        ctx.lineTo(tail[i].x, tail[i].y);
      }
    }
    ctx.stroke();

    // Draw tail ribbons
    for (let i = 2; i < tail.length; i += 3) {
      const node = tail[i];
      ctx.fillStyle = i % 2 === 0 ? '#FF6B6B' : '#FFE66D';
      ctx.beginPath();
      ctx.arc(node.x, node.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw kite
    ctx.save();
    ctx.translate(kite.x, kite.y);
    ctx.rotate(kite.angle);

    // Kite body (diamond shape)
    ctx.fillStyle = isTrickMode ? '#FF6B6B' : '#4ECDC4';
    ctx.beginPath();
    ctx.moveTo(0, -40);
    ctx.lineTo(25, 0);
    ctx.lineTo(0, 40);
    ctx.lineTo(-25, 0);
    ctx.closePath();
    ctx.fill();

    // Kite border
    ctx.strokeStyle = '#2C3E50';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Kite cross bars
    ctx.beginPath();
    ctx.moveTo(0, -40);
    ctx.lineTo(0, 40);
    ctx.moveTo(-25, 0);
    ctx.lineTo(25, 0);
    ctx.stroke();

    // Kite decorations
    ctx.fillStyle = '#FFE66D';
    ctx.beginPath();
    ctx.arc(0, 0, 8, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    // Draw ground
    ctx.fillStyle = '#90EE90';
    ctx.fillRect(0, 550, canvas.width, 50);
    
    // Draw grass details
    ctx.strokeStyle = '#228B22';
    ctx.lineWidth = 2;
    for (let i = 0; i < canvas.width; i += 20) {
      ctx.beginPath();
      ctx.moveTo(i, 550);
      ctx.lineTo(i + 5, 540);
      ctx.lineTo(i + 10, 550);
      ctx.stroke();
    }

    // Draw anchor point
    ctx.fillStyle = '#8B4513';
    ctx.beginPath();
    ctx.arc(anchorX, anchorY, 8, 0, Math.PI * 2);
    ctx.fill();
  }, [isTrickMode]);

  const gameLoop = useCallback(() => {
    updatePhysics();
    draw();
    animationRef.current = requestAnimationFrame(gameLoop);
  }, [updatePhysics, draw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = 800;
    canvas.height = 600;
    initTail(400, 300);

    const handleKeyDown = (e: KeyboardEvent) => {
      keysRef.current.add(e.key);
      
      // Trick keys
      if (e.key === '1') performTrick('loop');
      if (e.key === '2') performTrick('dive');
      if (e.key === '3') performTrick('figure8');
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysRef.current.delete(e.key);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    animationRef.current = requestAnimationFrame(gameLoop);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (trickTimerRef.current) {
        clearTimeout(trickTimerRef.current);
      }
    };
  }, [gameLoop, initTail, performTrick]);

  return (
    <div className="min-h-screen bg-slate-900 p-4">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-4 text-center text-3xl font-bold text-white">
          🪁 Kite Flying Simulation
        </h1>
        
        <div className="relative overflow-hidden rounded-lg border-4 border-slate-700 bg-slate-800">
          <canvas
            ref={canvasRef}
            className="block cursor-crosshair"
            style={{ imageRendering: 'pixelated' }}
          />
          
          {trickName && (
            <div className="absolute left-1/2 top-1/4 -translate-x-1/2 -translate-y-1/2">
              <div className="animate-bounce rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3 text-2xl font-bold text-white shadow-lg">
                {trickName}
              </div>
            </div>
          )}
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="rounded-lg bg-slate-800 p-4 text-center">
            <div className="text-sm text-slate-400">Altitude</div>
            <div className="text-2xl font-bold text-emerald-400">{altitude}m</div>
          </div>
          <div className="rounded-lg bg-slate-800 p-4 text-center">
            <div className="text-sm text-slate-400">String Tension</div>
            <div className="text-2xl font-bold text-amber-400">{tension}%</div>
          </div>
          <div className="rounded-lg bg-slate-800 p-4 text-center">
            <div className="text-sm text-slate-400">Wind Speed</div>
            <div className="text-2xl font-bold text-sky-400">{windSpeed.toFixed(1)}m/s</div>
          </div>
          <div className="rounded-lg bg-slate-800 p-4 text-center">
            <div className="text-sm text-slate-400">Trick Mode</div>
            <div className={`text-2xl font-bold ${isTrickMode ? 'text-pink-400' : 'text-slate-500'}`}>
              {isTrickMode ? 'Active!' : 'Ready'}
            </div>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-lg bg-slate-800 p-4">
            <h3 className="mb-2 font-semibold text-white">Controls</h3>
            <div className="space-y-1 text-sm text-slate-300">
              <div><span className="rounded bg-slate-700 px-2 py-1 font-mono">Arrow Keys</span> - Steer kite</div>
              <div><span className="rounded bg-slate-700 px-2 py-1 font-mono">W</span> - Release string</div>
              <div><span className="rounded bg-slate-700 px-2 py-1 font-mono">S</span> - Pull string</div>
            </div>
          </div>
          <div className="rounded-lg bg-slate-800 p-4">
            <h3 className="mb-2 font-semibold text-white">Tricks</h3>
            <div className="space-y-1 text-sm text-slate-300">
              <div><span className="rounded bg-slate-700 px-2 py-1 font-mono">1</span> - Loop</div>
              <div><span className="rounded bg-slate-700 px-2 py-1 font-mono">2</span> - Power Dive</div>
              <div><span className="rounded bg-slate-700 px-2 py-1 font-mono">3</span> - Figure 8</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
