import { useState, useEffect } from 'react';
import { Zap, MapPin, Search, Loader2, Sun, Target, Ruler, Download, X, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { analyzeLocation, checkHealth, getFileUrl, type AnalyzeResponse, type HealthResponse } from '@/lib/api';

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [lat, setLat] = useState('21.19504818778378');
  const [lon, setLon] = useState('72.90183627422766');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground dark">
        {/* Header */}
        <header className="border-b border-border/50 bg-card/50 backdrop-blur-xl sticky top-0 z-50">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 shadow-lg shadow-emerald-500/20">
                <Sun className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">SolarScan</h1>
                <p className="text-xs text-muted-foreground">Team Akatsuki</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {health ? (
                <Badge variant="outline" className="border-emerald-500/50 text-emerald-400 gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  System Online
                </Badge>
              ) : (
                <Badge variant="outline" className="border-red-500/50 text-red-400 gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  Offline
                </Badge>
              )}
            </div>
          </div>
        </header>

        <div className="flex min-h-[calc(100vh-73px)]">
          {/* Sidebar */}
          <aside className="w-[380px] border-r border-border/50 bg-card/30 backdrop-blur-xl p-6 flex flex-col">
            <div className="mb-8">
              <h2 className="text-3xl font-bold mb-2">
                Solar Intelligence
                <br />
                <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  for Everyone.
                </span>
              </h2>
              <p className="text-sm text-muted-foreground">
                Instant rooftop analysis using Satellite Imagery. Enter a location to estimate renewable potential.
              </p>
            </div>

            <Tabs defaultValue="single" className="flex-1">
              <TabsList className="w-full mb-6 bg-background/50">
                <TabsTrigger value="single" className="flex-1 gap-2">
                  <MapPin className="w-4 h-4" />
                  Single Point
                </TabsTrigger>
                <TabsTrigger value="batch" className="flex-1 gap-2">
                  <Zap className="w-4 h-4" />
                  Batch
                </TabsTrigger>
              </TabsList>

              <TabsContent value="single" className="space-y-4 mt-0">
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Latitude
                    </label>
                    <Input 
                      value={lat}
                      onChange={(e) => setLat(e.target.value)}
                      placeholder="21.1950..."
                      className="bg-background/50 border-border/50"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                      Longitude
                    </label>
                    <Input 
                      value={lon}
                      onChange={(e) => setLon(e.target.value)}
                      placeholder="72.9018..."
                      className="bg-background/50 border-border/50"
                    />
                  </div>
                </div>

                <Button 
                  onClick={handleAnalyze}
                  disabled={loading || !lat || !lon}
                  className="w-full bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white shadow-lg shadow-emerald-500/20"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Analyze Location
                    </>
                  )}
                </Button>

                {error && (
                  <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    {error}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="batch" className="mt-0">
                <Card className="border-dashed border-2 border-border/50 bg-background/30">
                  <CardContent className="p-8 text-center">
                    <Zap className="w-10 h-10 mx-auto mb-3 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground mb-3">
                      Upload CSV/Excel file with coordinates
                    </p>
                    <Button variant="outline" size="sm">
                      Upload File
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            <Separator className="my-6" />

            <div className="text-xs text-muted-foreground">
              <p className="mb-1">Model: <span className="text-foreground font-medium">{health?.model_type || '—'}</span></p>
              <p>SAHI: <span className="text-foreground font-medium">{health?.use_sahi ? 'Enabled' : 'Disabled'}</span></p>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 relative bg-gradient-to-br from-background via-background to-emerald-950/10">
            {/* Map placeholder / Results view */}
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="relative w-24 h-24 mx-auto mb-6">
                    <div className="absolute inset-0 rounded-full border-4 border-emerald-500/20" />
                    <div className="absolute inset-0 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin" />
                    <Sun className="absolute inset-0 m-auto w-10 h-10 text-emerald-500" />
                  </div>
                  <p className="text-lg font-medium">Analyzing satellite imagery...</p>
                  <p className="text-sm text-muted-foreground mt-1">This may take a few seconds</p>
                </div>
              </div>
            ) : result && showResult ? (
              <div className="absolute inset-0 flex">
                {/* Overlay Image */}
                <div className="flex-1 relative">
                  <img
                    src={getFileUrl(result.overlay_url)}
                    alt="Detection overlay"
                    className="absolute inset-0 w-full h-full object-contain bg-black/50"
                  />
                  
                  {/* Download button */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="secondary"
                        className="absolute top-4 right-4"
                        onClick={() => window.open(getFileUrl(result.overlay_url), '_blank')}
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Download overlay</TooltipContent>
                  </Tooltip>

                  {/* Status badge */}
                  <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-center">
                    <Badge 
                      className={`text-sm px-4 py-1.5 ${
                        result.has_solar 
                          ? 'bg-emerald-500/90 text-white' 
                          : 'bg-red-500/90 text-white'
                      }`}
                    >
                      {result.has_solar ? 'SOLAR DETECTED' : 'NO SOLAR FOUND'}
                    </Badge>
                    <p className="text-lg font-semibold mt-2">Assessment Complete</p>
                    <p className="text-xs text-muted-foreground">
                      Lat: {result.lat.toFixed(5)} | Lon: {result.lon.toFixed(5)}
                    </p>
                  </div>
                </div>

                {/* Results Panel */}
                <div className="w-[340px] bg-card/95 backdrop-blur-xl border-l border-border/50 p-6 overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">Confidence</p>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold">
                          {(result.confidence * 100).toFixed(1)}%
                        </span>
                        <Badge 
                          variant="outline" 
                          className={result.confidence > 0.7 ? 'border-emerald-500 text-emerald-400' : 'border-yellow-500 text-yellow-400'}
                        >
                          {result.confidence > 0.7 ? 'HIGH' : 'MEDIUM'}
                        </Badge>
                      </div>
                    </div>
                    <Button 
                      size="icon" 
                      variant="ghost"
                      onClick={() => setShowResult(false)}
                    >
                      <X className="w-5 h-5" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <Card className="bg-background/50 border-border/30">
                      <CardContent className="p-4">
                        <p className="text-xs text-muted-foreground mb-1">METHOD</p>
                        <p className="font-medium">Initial</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-background/50 border-border/30">
                      <CardContent className="p-4">
                        <p className="text-xs text-muted-foreground mb-1">BUFFER</p>
                        <p className="font-medium">{result.buffer_radius_sqft} sqft</p>
                      </CardContent>
                    </Card>
                  </div>

                  <Separator className="my-6" />

                  <div className="space-y-6">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="w-4 h-4 text-emerald-500" />
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Est. Area</p>
                      </div>
                      <p className="text-3xl font-bold">{result.pv_area_sqm_est.toFixed(1)} <span className="text-lg font-normal text-muted-foreground">m²</span></p>
                    </div>

                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Ruler className="w-4 h-4 text-cyan-500" />
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Distance from Center</p>
                      </div>
                      <p className="text-3xl font-bold">{result.euclidean_distance_m_est.toFixed(1)} <span className="text-lg font-normal text-muted-foreground">m</span></p>
                    </div>
                  </div>

                  <Separator className="my-6" />

                  <div className="flex items-center gap-2 text-sm">
                    {result.qc_status === 'VERIFIABLE' ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span className="text-emerald-400">Verifiable</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4 text-yellow-500" />
                        <span className="text-yellow-400">Not Verifiable</span>
                      </>
                    )}
                  </div>

                  <Button 
                    className="w-full mt-6"
                    variant="outline"
                    onClick={() => setShowResult(false)}
                  >
                    Done
                  </Button>
                </div>
              </div>
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center max-w-md">
                  <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center">
                    <MapPin className="w-10 h-10 text-emerald-500" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Enter Coordinates</h3>
                  <p className="text-muted-foreground">
                    Input latitude and longitude to analyze satellite imagery for solar panel detection.
                  </p>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </TooltipProvider>
  );
}

export default App;
