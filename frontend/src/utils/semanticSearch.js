const VECTOR_DIM = 256;

const tokenize = (text) => {
    if (!text) return [];
    return (text.toLowerCase().match(/\b\w+\b/g) || []);
};

const hashToken = (token) => {
    let hash = 0;
    for (let i = 0; i < token.length; i += 1) {
        hash = ((hash << 5) - hash) + token.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash) % VECTOR_DIM;
};

export const embedText = (text) => {
    const vec = Array(VECTOR_DIM).fill(0);
    const tokens = tokenize(text);
    tokens.forEach((token) => {
        vec[hashToken(token)] += 1;
    });
    const norm = Math.sqrt(vec.reduce((sum, value) => sum + value * value, 0));
    if (!norm) return vec;
    return vec.map((value) => value / norm);
};

export const cosineSimilarity = (vecA, vecB) => {
    if (!vecA || !vecB || vecA.length !== vecB.length) return 0;
    let dot = 0;
    let normA = 0;
    let normB = 0;
    for (let i = 0; i < vecA.length; i += 1) {
        dot += vecA[i] * vecB[i];
        normA += vecA[i] * vecA[i];
        normB += vecB[i] * vecB[i];
    }
    if (!normA || !normB) return 0;
    return dot / Math.sqrt(normA * normB);
};
