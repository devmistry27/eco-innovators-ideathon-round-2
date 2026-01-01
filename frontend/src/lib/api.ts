const API_BASE = 'http://localhost:8000';

export interface AnalyzeRequest {
    lat: number;
    lon: number;
    sample_id?: string;
}

export interface AnalyzeResponse {
    sample_id: string;
    lat: number;
    lon: number;
    has_solar: boolean;
    confidence: number;
    pv_area_sqm_est: number;
    buffer_radius_sqft: number;
    euclidean_distance_m_est: number;
    qc_status: string;
    image_url: string;
    overlay_url: string;
}

export interface HealthResponse {
    status: string;
    model_type: string;
    use_sahi: boolean;
}

export async function checkHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error('API unavailable');
    return res.json();
}

export async function analyzeLocation(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Analysis failed');
    }
    return res.json();
}

export function getFileUrl(path: string): string {
    return `${API_BASE}${path}`;
}
