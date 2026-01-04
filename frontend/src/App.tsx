import { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import { Zap, MapPin, Search, Loader2, Target, Ruler, Download, X, CheckCircle2, XCircle, Crosshair, ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Progress } from '@/components/ui/progress';
import { analyzeLocation, checkHealth, getFileUrl, type AnalyzeResponse, type HealthResponse } from '@/lib/api';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { read, utils } from 'xlsx';

// Fix default marker icon
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const blueIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Map click handler
function MapClickHandler({ onLocationSelect }: { onLocationSelect: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Map center updater
function MapCenterUpdater({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, map.getZoom(), { duration: 1.5 });
  }, [center, map]);
  return null;
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [lat, setLat] = useState('21.19504818778378');
  const [lon, setLon] = useState('72.90183627422766');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Batch State
  const [batchResults, setBatchResults] = useState<AnalyzeResponse[]>([]);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });

  const mapCenter: [number, number] = [parseFloat(lat) || 21.195, parseFloat(lon) || 72.901];

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const handleLocationSelect = useCallback((newLat: number, newLng: number) => {
    setLat(newLat.toFixed(8));
    setLon(newLng.toFixed(8));
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=1`
      );
      const data = await response.json();
      
      if (data && data.length > 0) {
        setLat(data[0].lat);
        setLon(data[0].lon);
      } else {
        setError('Location not found');
      }
    } catch {
      setError('Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await analyzeLocation({
        lat: parseFloat(lat),
        lon: parseFloat(lon),
      });
      setResult(response);
      setShowResult(true);
      setSidebarOpen(false); // Close main sidebar when showing results
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleUseMyLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLat(position.coords.latitude.toFixed(8));
          setLon(position.coords.longitude.toFixed(8));
        },
        () => setError('Could not get your location')
      );
    }
  };

  return (
    <TooltipProvider>
      <div className="h-screen w-screen overflow-hidden relative bg-black font-sans">
        
        {/* Floating Header */}
        <header className="absolute top-0 left-0 right-0 z-[1000] pb-4 pt-7 px-4 pointer-events-none">
          <div className="container mx-auto flex w-screen justify-center items-center">
            {/* Logo */}
            <div className="pointer-events-auto bg-black/40 backdrop-blur-xl px-5 py-2.5 rounded-full border border-white/10 shadow-2xl flex items-center gap-3">
               <div>
                  <h1 className="text-xl font-bold tracking-tight text-white leading-none">SolarSight</h1>
               </div>
               <div className="h-4 w-[1px] bg-white/20"></div>
               <p className="text-[11px] text-zinc-400 font-medium tracking-wide uppercase">Team Akatsuki</p>
            </div>
          </div>
        </header>

        {/* Floating Sidebar */}
        <div 
          className={`absolute top-24 left-6 z-[1000] w-[380px] bg-black/60 backdrop-blur-2xl border border-white/10 shadow-2xl rounded-3xl transition-all duration-500 ease-in-out ${
            sidebarOpen && !showResult ? 'translate-x-0 opacity-100' : '-translate-x-[150%] opacity-0'
          }`}
        >
          <div className="p-6">
            <div className="mb-6">
              <h2 className="text-3xl font-bold mb-2 tracking-tight text-white">
                Solar Potential
              </h2>
              <p className="text-sm text-zinc-400 leading-relaxed font-light">
                Unlock the solar potential of any location. Analyze satellite imagery instantly with our AI.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex gap-2 relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search city, address..."
                  className="pl-9 bg-white/5 border-white/10 text-white placeholder:text-zinc-500 focus-visible:ring-blue-500/50 rounded-xl"
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button 
                  size="icon" 
                  className="bg-white/10 hover:bg-white/20 text-white border border-white/5 rounded-xl transition-colors"
                  onClick={handleSearch}
                  disabled={searching}
                >
                  {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronLeft className="w-4 h-4 rotate-180" />}
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                 <Button 
                   variant="outline" 
                   size="sm"
                   className="w-full bg-white/5 border-white/10 text-zinc-400 hover:text-white hover:bg-white/10 rounded-xl"
                   onClick={handleUseMyLocation}
                >
                  <Crosshair className="w-3.5 h-3.5 mr-2" />
                  Locate Me
                </Button>
                <div className="flex items-center justify-end text-[10px] text-zinc-500 font-mono uppercase tracking-wider">
                  {lat ? `${parseFloat(lat).toFixed(4)}, ${parseFloat(lon).toFixed(4)}` : 'No Location Selected'}
                </div>
              </div>

              <Tabs defaultValue="single" className="w-full">
                <TabsList className="w-full bg-black/40 border border-white/10 p-1 rounded-xl h-auto">
                  <TabsTrigger 
                    value="single" 
                    className="flex-1 py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:text-black data-[state=active]:font-semibold transition-all cursor-pointer"
                  >
                    Single Point
                  </TabsTrigger>
                  <TabsTrigger 
                    value="batch" 
                    className="flex-1 py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:text-black data-[state=active]:font-semibold transition-all cursor-pointer"
                  >
                    Batch Analysis
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="single" className="mt-4 space-y-4">
                   <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                     <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                          <MapPin className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-blue-100">Ready to Analyze</p>
                          <p className="text-xs text-blue-400/70 mt-0.5">Selected coordinates are valid.</p>
                        </div>
                     </div>
                   </div>

                  <Button 
                    onClick={handleAnalyze}
                    disabled={loading || !lat || !lon}
                    className="w-full py-6 text-base font-medium bg-white text-black hover:bg-zinc-200 shadow-xl shadow-white/5 border-0 rounded-xl transition-all cursor-pointer"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      'Start Analysis'
                    )}
                  </Button>
                </TabsContent>
                
                <TabsContent value="batch" className="mt-4">
                  {loading && batchProgress.total > 0 ? (
                    // 1. PROCESSING STATE
                    <Card className="bg-zinc-900/50 border-zinc-800">
                      <CardContent className="p-8 text-center space-y-6">
                        <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
                          <div className="absolute inset-0 rounded-full border-t-2 border-blue-500 animate-spin"></div>
                          <Loader2 className="w-8 h-8 text-blue-500 animate-pulse" />
                        </div>
                        <div className="space-y-2">
                           <h3 className="text-lg font-medium text-white">Analyzing Satellite Imagery</h3>
                           <p className="text-sm text-zinc-400">Processing site {batchProgress.current} of {batchProgress.total}</p>
                        </div>
                        <Progress value={(batchProgress.current / batchProgress.total) * 100} className="h-2" />
                      </CardContent>
                    </Card>
                  ) : batchResults.length > 0 ? (
                    // 2. RESULTS LIST STATE
                    <div className="space-y-4">
                       <div className="flex items-center justify-between px-1">
                          <h3 className="text-sm font-medium text-zinc-400">Analysis Complete ({batchResults.length})</h3>
                          <Button variant="ghost" size="sm" onClick={() => { setBatchResults([]); setBatchProgress({current:0, total:0}); }} className="h-8 text-xs hover:text-white">
                             New Batch
                          </Button>
                       </div>
                       
                       <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                          {batchResults.map((res, i) => (
                             <div 
                                key={i}
                                onClick={() => { setResult(res); setShowResult(true); setSidebarOpen(false); }}
                                className="group flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 transition-all cursor-pointer"
                             >
                                <div className="flex items-center gap-3">
                                   <div className={`p-2 rounded-lg ${res.has_solar ? 'bg-blue-500/20 text-blue-400' : 'bg-red-500/10 text-red-400'}`}>
                                      {res.has_solar ? <Zap className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                   </div>
                                   <div>
                                      <p className="text-sm font-medium text-white group-hover:text-blue-200 transition-colors">
                                         {res.lat.toFixed(4)}, {res.lon.toFixed(4)}
                                      </p>
                                      <div className="flex items-center gap-2 mt-0.5">
                                         <Badge variant="outline" className="text-[10px] h-4 px-1 border-white/10 text-zinc-500">
                                            {(res.confidence * 100).toFixed(0)}% Conf
                                         </Badge>
                                         <span className="text-[10px] text-zinc-600">ID: #{i+1}</span>
                                      </div>
                                   </div>
                                </div>
                                <ChevronLeft className="w-4 h-4 text-zinc-600 group-hover:text-white rotate-180 transition-colors" />
                             </div>
                          ))}
                       </div>
                    </div>
                  ) : (
                    // 3. UPLOAD STATE (Default)
                    <Card className="border-2 border-dashed border-zinc-800 bg-transparent rounded-xl hover:border-zinc-700 hover:bg-zinc-900/30 transition-all group cursor-pointer" onClick={() => document.getElementById('csvUpload')?.click()}>
                      <CardContent className="p-8 flex flex-col items-center justify-center text-center">
                         <input
                           type="file"
                           id="csvUpload"
                           accept=".csv, .xlsx, .xls"
                           className="hidden"
                           onChange={async (e) => {
                             const file = e.target.files?.[0];
                             if (!file) return;
                             
                             setLoading(true);
                             setBatchResults([]);
                             
                             try {
                               const data = await file.arrayBuffer();
                               const workbook = read(data);
                               const worksheet = workbook.Sheets[workbook.SheetNames[0]];
                               const jsonData = utils.sheet_to_json(worksheet, { header: 1 });
                               
                               if (jsonData.length < 2) {
                                  setError("File empty or missing headers");
                                  setLoading(false);
                                  return;
                               }

                               // Normalize headers
                               const headers = (jsonData[0] as string[]).map(h => h?.toString().toLowerCase() || '');
                               const latIdx = headers.findIndex(h => h.includes('lat'));
                               const lonIdx = headers.findIndex(h => h.includes('lon'));
                               
                               if (latIdx === -1 || lonIdx === -1) {
                                 setError("File must contain 'lat' and 'lon' columns");
                                 setLoading(false);
                                 return;
                               }

                               // Filter valid rows first to get total count
                               const validRows = [];
                               for(let i=1; i<jsonData.length; i++) {
                                  const row = jsonData[i] as any[];
                                  if(row && row.length > 0) {
                                     const lat = parseFloat(row[latIdx]);
                                     const lon = parseFloat(row[lonIdx]);
                                     if(!isNaN(lat) && !isNaN(lon)) {
                                        validRows.push({lat, lon});
                                     }
                                  }
                               }

                               setBatchProgress({ current: 0, total: validRows.length });
                               const results = [];
                               
                               for(let i=0; i<validRows.length; i++) {
                                 const {lat, lon} = validRows[i];
                                 try {
                                    // Simulated delay for UX if API is too fast, or actual API call
                                    const res = await analyzeLocation({ lat, lon });
                                    results.push(res);
                                 } catch (err) {
                                   console.error(`Failed to analyze ${lat},${lon}`, err);
                                   // Optionally push a specific error result structure
                                 }
                                 setBatchProgress(prev => ({ ...prev, current: i + 1 }));
                               }
                               
                               setBatchResults(results);
                               setLoading(false);
                             } catch (err) {
                               console.error("File parse error:", err);
                               setError("Failed to parse file.");
                               setLoading(false);
                             }
                           }}
                         />
                         <div className="p-4 rounded-full bg-zinc-900 mb-4 group-hover:bg-blue-500/10 group-hover:scale-110 transition-all duration-300">
                            <Zap className="w-6 h-6 text-zinc-500 group-hover:text-blue-400" />
                         </div>
                         <p className="text-sm text-zinc-400 mb-2 group-hover:text-white transition-colors">Click to upload CSV or Excel</p>
                         <div className="flex gap-2">
                            <Badge variant="outline" className="border-zinc-800 text-zinc-600 bg-zinc-900/50">.CSV</Badge>
                            <Badge variant="outline" className="border-zinc-800 text-zinc-600 bg-zinc-900/50">.XLSX</Badge>
                         </div>
                      </CardContent>
                    </Card>
                  )}
                 </TabsContent>
              </Tabs>
            </div>
            
            <div className="mt-6 pt-6 border-t border-white/5 flex justify-between items-center text-xs text-zinc-500">
               <span>Model: <span className="text-zinc-300">{health?.model_type || 'Unknown'}</span></span>
            </div>
          </div>
        </div>

        {/* Results Overlay */}
        {showResult && result && (
           <div className="absolute inset-0 z-[1000] flex animate-in fade-in duration-300">
              {/* Dimmed Background */}
              <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setShowResult(false)} />

              {/* Content Container */}
              <div className="relative w-full h-full flex items-center justify-center p-8 pointer-events-none">
                 <div className="flex w-full max-w-6xl h-[80vh] bg-zinc-950/90 border border-white/10 rounded-3xl overflow-hidden shadow-2xl pointer-events-auto flex-col md:flex-row">
                    
                    {/* Visual Side */}
                    <div className="flex-1 relative bg-black/50 group">
                       <img 
                          src={getFileUrl(result.overlay_url)} 
                          className="absolute inset-0 w-full h-full object-contain p-4"
                          alt="Analysis Result"
                       />
                       
                       <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button size="icon" variant="secondary" onClick={() => window.open(getFileUrl(result.overlay_url), '_blank')}>
                             <Download className="w-4 h-4" />
                          </Button>
                       </div>
                    </div>

                    {/* Data Side */}
                    <div className="w-full md:w-[400px] bg-black/40 backdrop-blur-2xl p-8 border-l border-white/5 overflow-y-auto">
                        <div className="flex justify-between items-start mb-8">
                           <div>
                              <div className="flex items-center gap-2 mb-2">
                                 {result.has_solar ? (
                                    <div className="flex items-center gap-2 text-blue-400">
                                       <CheckCircle2 className="w-5 h-5" />
                                       <span className="font-bold tracking-tight">SOLAR DETECTED</span>
                                    </div>
                                 ) : (
                                    <div className="flex items-center gap-2 text-red-400">
                                       <XCircle className="w-5 h-5" />
                                       <span className="font-bold tracking-tight">NO SOLAR FOUND</span>
                                    </div>
                                 )}
                              </div>
                              <h3 className="text-2xl font-bold text-white">Analysis Report</h3>
                           </div>
                           <Button size="icon" variant="ghost" onClick={() => { setShowResult(false); setSidebarOpen(true); }} className="text-zinc-500 hover:text-white">
                              <X className="w-6 h-6" />
                           </Button>
                        </div>

                        <div className="space-y-6">
                           <div className="grid grid-cols-2 gap-4">
                              <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                 <p className="text-xs text-zinc-400 uppercase tracking-wider mb-1">Confidence</p>
                                 <p className="text-2xl font-bold text-white">{(result.confidence * 100).toFixed(0)}%</p>
                              </div>
                              <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                 <p className="text-xs text-zinc-400 uppercase tracking-wider mb-1">Area Est.</p>
                                 <p className="text-2xl font-bold text-white">{result.pv_area_sqm_est.toFixed(0)} <span className="text-sm font-normal text-zinc-500">m²</span></p>
                              </div>
                           </div>

                           <div className="space-y-4">
                              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                                  <div className="flex items-center gap-3">
                                     <Target className="w-5 h-5 text-blue-500" />
                                     <div>
                                        <p className="text-sm font-medium text-white">Center Offset</p>
                                        <p className="text-xs text-zinc-500">Distance from cursor</p>
                                     </div>
                                  </div>
                                  <span className="text-lg font-mono text-blue-400">{result.euclidean_distance_m_est.toFixed(1)}m</span>
                              </div>
                              
                              <div className="flex items-center justify-between p-4 rounded-xl bg-white/5">
                                  <div className="flex items-center gap-3">
                                     <Ruler className="w-5 h-5 text-indigo-500" />
                                     <div>
                                        <p className="text-sm font-medium text-white">Total Span</p>
                                        <p className="text-xs text-zinc-500">Approximate coverage</p>
                                     </div>
                                  </div>
                                  <span className="text-lg font-mono text-indigo-400">{result.buffer_radius_sqft} sqft</span>
                              </div>
                           </div>
                        </div>

                        <div className="mt-8 pt-6 border-t border-white/5">
                           <Button className="w-full bg-white text-black hover:bg-zinc-200 rounded-xl py-6" onClick={() => { setShowResult(false); setSidebarOpen(true); }}>
                              Close Report
                           </Button>
                        </div>
                    </div>
                 </div>
              </div>
           </div>
        )}

        {/* Restore Sidebar Button (when closed) */}
        {!sidebarOpen && !showResult && (
           <Button 
            className="absolute top-24 left-6 z-[1000] bg-black/80 border border-white/10 shadow-xl text-white hover:bg-black rounded-xl"
            onClick={() => setSidebarOpen(true)}
           >
              Show Menu
           </Button>
        )}

        {/* Map Layer */}
        <div className="absolute inset-0 z-0 bg-black">
          <MapContainer
            center={mapCenter}
            zoom={18}
            className="w-full h-full"
            style={{ background: '#09090b' }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; Google'
              url="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
              maxZoom={22}
            />
            <MapClickHandler onLocationSelect={handleLocationSelect} />
            <MapCenterUpdater center={mapCenter} />
            {lat && lon && (
              <Marker 
                position={[parseFloat(lat), parseFloat(lon)]} 
                icon={blueIcon}
              />
            )}
          </MapContainer>
        </div>
      </div>
    </TooltipProvider>
  );
}

export default App;
