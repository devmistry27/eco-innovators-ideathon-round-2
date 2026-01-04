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
import { analyzeLocation, checkHealth, getFileUrl, type AnalyzeResponse, type HealthResponse } from '@/lib/api';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

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

            {/* Status */}
            {/* <div className="pointer-events-auto">
              {health ? (
                <Badge variant="outline" className="bg-blue-500/10 border-blue-500/20 text-blue-400 gap-2 px-3 py-1.5 backdrop-blur-md rounded-full">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                  </span>
                  System Online
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-red-500/10 border-red-500/20 text-red-400 gap-2 px-3 py-1.5 backdrop-blur-md rounded-full">
                   <div className="h-2 w-2 rounded-full bg-red-500" />
                  Offline
                </Badge>
              )}
            </div> */}
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
                    <Card className="border-2 border-dashed border-zinc-800 bg-transparent rounded-xl">
                      <CardContent className="p-8 flex flex-col items-center justify-center text-center">
                         <div className="p-4 rounded-full bg-zinc-900 mb-4">
                            <Zap className="w-6 h-6 text-zinc-500" />
                         </div>
                         <p className="text-sm text-zinc-400 mb-4">Drag & drop CSV file here</p>
                         <Button variant="secondary" size="sm" className="bg-zinc-800 text-zinc-300 hover:text-white rounded-lg">Browse Files</Button>
                      </CardContent>
                    </Card>
                 </TabsContent>
              </Tabs>
            </div>
            
            <div className="mt-6 pt-6 border-t border-white/5 flex justify-between items-center text-xs text-zinc-500">
               <span>Model: <span className="text-zinc-300">{health?.model_type || 'Unknown'}</span></span>
               <span>SAHI: <span className={health?.use_sahi ? "text-blue-400" : "text-zinc-300"}>{health?.use_sahi ? 'Active' : 'Off'}</span></span>
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
