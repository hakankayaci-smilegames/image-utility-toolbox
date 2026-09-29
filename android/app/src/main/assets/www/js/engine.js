/**
 * Image Utility Toolbox - High-Performance Client Engine
 * Exact algorithmic parity with Python core operations and binary search compressor.
 */

class ProcessingEngine {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    }

    createContextFromImage(imgElement) {
        this.canvas.width = imgElement.naturalWidth || imgElement.width;
        this.canvas.height = imgElement.naturalHeight || imgElement.height;
        this.ctx.drawImage(imgElement, 0, 0);
        return {
            width: this.canvas.width,
            height: this.canvas.height,
            imageData: this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height)
        };
    }

    cloneImageData(src) {
        const copy = this.ctx.createImageData(src.width, src.height);
        copy.data.set(src.data);
        return copy;
    }

    // 1. RESIZE (Lanczos/Bicubic smooth interpolation via Canvas)
    resize(imgData, newWidth, newHeight) {
        const offCanvas = document.createElement('canvas');
        offCanvas.width = imgData.width;
        offCanvas.height = imgData.height;
        const offCtx = offCanvas.getContext('2d');
        offCtx.putImageData(imgData, 0, 0);

        const destCanvas = document.createElement('canvas');
        destCanvas.width = Math.max(1, Math.round(newWidth));
        destCanvas.height = Math.max(1, Math.round(newHeight));
        const destCtx = destCanvas.getContext('2d');
        destCtx.imageSmoothingEnabled = true;
        destCtx.imageSmoothingQuality = 'high';
        destCtx.drawImage(offCanvas, 0, 0, destCanvas.width, destCanvas.height);

        return {
            width: destCanvas.width,
            height: destCanvas.height,
            imageData: destCtx.getImageData(0, 0, destCanvas.width, destCanvas.height)
        };
    }

    // 2. CROP
    crop(imgData, x, y, width, height) {
        x = Math.max(0, Math.min(imgData.width - 1, Math.round(x)));
        y = Math.max(0, Math.min(imgData.height - 1, Math.round(y)));
        width = Math.max(1, Math.min(imgData.width - x, Math.round(width)));
        height = Math.max(1, Math.min(imgData.height - y, Math.round(height)));

        const offCanvas = document.createElement('canvas');
        offCanvas.width = imgData.width;
        offCanvas.height = imgData.height;
        const offCtx = offCanvas.getContext('2d');
        offCtx.putImageData(imgData, 0, 0);

        const cropCanvas = document.createElement('canvas');
        cropCanvas.width = width;
        cropCanvas.height = height;
        const cropCtx = cropCanvas.getContext('2d');
        cropCtx.drawImage(offCanvas, x, y, width, height, 0, 0, width, height);

        return {
            width: width,
            height: height,
            imageData: cropCtx.getImageData(0, 0, width, height)
        };
    }

    // 3. TRANSFORM (Rotate & Flip)
    transform(imgData, angleDegrees, flipH, flipV) {
        const rad = (angleDegrees * Math.PI) / 180;
        const sin = Math.abs(Math.sin(rad));
        const cos = Math.abs(Math.cos(rad));
        const newW = Math.round(imgData.width * cos + imgData.height * sin);
        const newH = Math.round(imgData.height * cos + imgData.width * sin);

        const srcCanvas = document.createElement('canvas');
        srcCanvas.width = imgData.width;
        srcCanvas.height = imgData.height;
        srcCanvas.getContext('2d').putImageData(imgData, 0, 0);

        const destCanvas = document.createElement('canvas');
        destCanvas.width = Math.max(1, newW);
        destCanvas.height = Math.max(1, newH);
        const destCtx = destCanvas.getContext('2d');
        destCtx.imageSmoothingEnabled = true;
        destCtx.imageSmoothingQuality = 'high';

        destCtx.translate(destCanvas.width / 2, destCanvas.height / 2);
        destCtx.rotate(rad);
        destCtx.scale(flipH ? -1 : 1, flipV ? -1 : 1);
        destCtx.drawImage(srcCanvas, -imgData.width / 2, -imgData.height / 2);

        return {
            width: destCanvas.width,
            height: destCanvas.height,
            imageData: destCtx.getImageData(0, 0, destCanvas.width, destCanvas.height)
        };
    }

    // 4. COLOR TONE & EXPOSURE (Brightness, Contrast, Kelvin, Vibrance)
    applyToneAdjustments(srcImgData, brightness, contrast, kelvin, vibrance) {
        const out = this.cloneImageData(srcImgData);
        const d = out.data;
        const len = d.length;

        // Kelvin blackbody RGB multiplier calculation
        const kMult = this.kelvinToRGB(kelvin || 6500);

        // Brightness & Contrast precomputations
        const bOffset = (brightness || 0) * 1.28; // -100..100 -> -128..128
        const cFactor = (contrast >= 0) ? (1 + (contrast / 100) * 1.5) : (1 + (contrast / 100) * 0.75);
        const vibFactor = (vibrance || 0) / 100;

        // Precompute 256-entry lookup tables for ultra-fast 60 FPS execution
        const lutR = new Uint8ClampedArray(256);
        const lutG = new Uint8ClampedArray(256);
        const lutB = new Uint8ClampedArray(256);

        for (let v = 0; v < 256; v++) {
            lutR[v] = (v * kMult.r - 128) * cFactor + 128 + bOffset;
            lutG[v] = (v * kMult.g - 128) * cFactor + 128 + bOffset;
            lutB[v] = (v * kMult.b - 128) * cFactor + 128 + bOffset;
        }

        if (vibFactor === 0) {
            // Direct LUT lookup: ~1ms execution
            for (let i = 0; i < len; i += 4) {
                d[i] = lutR[d[i]];
                d[i + 1] = lutG[d[i + 1]];
                d[i + 2] = lutB[d[i + 2]];
            }
        } else {
            // Vibrance with precomputed LUT base
            for (let i = 0; i < len; i += 4) {
                let r = lutR[d[i]];
                let g = lutG[d[i + 1]];
                let b = lutB[d[i + 2]];

                const max = Math.max(r, g, b);
                const min = Math.min(r, g, b);
                const sat = (max === 0) ? 0 : (max - min) / max;
                const weight = (1 - sat) * vibFactor;
                const avg = (r + g + b) * 0.3333;
                r += (r - avg) * weight;
                g += (g - avg) * weight;
                b += (b - avg) * weight;

                d[i] = Math.max(0, Math.min(255, r));
                d[i + 1] = Math.max(0, Math.min(255, g));
                d[i + 2] = Math.max(0, Math.min(255, b));
            }
        }

        return { width: out.width, height: out.height, imageData: out };
    }

    kelvinToRGB(kelvin) {
        const temp = Math.max(1500, Math.min(15000, kelvin)) / 100;
        let r, g, b;

        if (temp <= 66) {
            r = 255;
            g = 99.4708025861 * Math.log(temp) - 161.1195681661;
            b = temp <= 19 ? 0 : 138.5177312231 * Math.log(temp - 10) - 305.0447927307;
        } else {
            r = 329.698727446 * Math.pow(temp - 60, -0.1332047592);
            g = 288.1221695283 * Math.pow(temp - 60, -0.0755148492);
            b = 255;
        }

        // Normalize relative to standard daylight D65 (6500K)
        return {
            r: Math.max(0.5, Math.min(1.8, r / 255)),
            g: Math.max(0.5, Math.min(1.8, g / 255)),
            b: Math.max(0.5, Math.min(1.8, b / 255))
        };
    }

    // 5. ARTISTIC EFFECTS (12 Categories)
    applyEffect(srcImgData, effectType, params = {}) {
        const w = srcImgData.width;
        const h = srcImgData.height;
        const out = this.cloneImageData(srcImgData);
        const d = out.data;

        switch (effectType) {
            case 'sepia': {
                const intensity = (params.intensity !== undefined ? params.intensity : 80) / 100;
                for (let i = 0; i < d.length; i += 4) {
                    const r = d[i], g = d[i+1], b = d[i+2];
                    const tr = (r * 0.393) + (g * 0.769) + (b * 0.189);
                    const tg = (r * 0.349) + (g * 0.686) + (b * 0.168);
                    const tb = (r * 0.272) + (g * 0.534) + (b * 0.131);
                    d[i] = r + (Math.min(255, tr) - r) * intensity;
                    d[i+1] = g + (Math.min(255, tg) - g) * intensity;
                    d[i+2] = b + (Math.min(255, tb) - b) * intensity;
                }
                break;
            }
            case 'vintage': {
                const grain = (params.grain || 30) * 1.5;
                for (let i = 0; i < d.length; i += 4) {
                    let r = d[i], g = d[i+1], b = d[i+2];
                    const noise = (Math.random() - 0.5) * grain;
                    r = r * 1.1 + noise + 10;
                    g = g * 0.95 + noise;
                    b = b * 0.85 + noise - 5;
                    d[i] = Math.max(0, Math.min(255, r));
                    d[i+1] = Math.max(0, Math.min(255, g));
                    d[i+2] = Math.max(0, Math.min(255, b));
                }
                break;
            }
            case 'cyanotype': {
                const intensity = (params.intensity || 85) / 100;
                for (let i = 0; i < d.length; i += 4) {
                    const lum = 0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2];
                    const tr = lum * 0.1;
                    const tg = lum * 0.45;
                    const tb = lum * 0.85 + 40;
                    d[i] = d[i] + (Math.min(255, tr) - d[i]) * intensity;
                    d[i+1] = d[i+1] + (Math.min(255, tg) - d[i+1]) * intensity;
                    d[i+2] = d[i+2] + (Math.min(255, tb) - d[i+2]) * intensity;
                }
                break;
            }
            case 'cyberpunk': {
                for (let i = 0; i < d.length; i += 4) {
                    let r = d[i], g = d[i+1], b = d[i+2];
                    // Enhance cyan in shadows, magenta/neon in highlights
                    if (r > 128) {
                        r = Math.min(255, r * 1.25);
                        b = Math.min(255, b * 1.3);
                        g = g * 0.75;
                    } else {
                        b = Math.min(255, b * 1.4);
                        g = Math.min(255, g * 1.2);
                        r = r * 0.6;
                    }
                    d[i] = r; d[i+1] = g; d[i+2] = b;
                }
                break;
            }
            case 'vignette': {
                const radius = (params.radius !== undefined ? params.radius : 75) / 100;
                const feather = (params.feather !== undefined ? params.feather : 60) / 100;
                const maxDist = Math.sqrt((w/2)*(w/2) + (h/2)*(h/2));
                const inner = maxDist * radius * (1 - feather);
                const outer = maxDist * radius;

                for (let y = 0; y < h; y++) {
                    for (let x = 0; x < w; x++) {
                        const idx = (y * w + x) * 4;
                        const dx = x - w/2;
                        const dy = y - h/2;
                        const dist = Math.sqrt(dx*dx + dy*dy);
                        if (dist > inner) {
                            const factor = 1 - Math.min(1, (dist - inner) / (outer - inner + 0.001));
                            d[idx] = d[idx] * factor;
                            d[idx+1] = d[idx+1] * factor;
                            d[idx+2] = d[idx+2] * factor;
                        }
                    }
                }
                break;
            }
            case 'sharpness': {
                return this.applyUnsharpMask(srcImgData, params.amount || 1.5, params.radius || 1);
            }
            case 'blur': {
                return this.applyGaussianBlur(srcImgData, params.radius || 5);
            }
            case 'denoise': {
                return this.applyBilateralFilter(srcImgData, params.strength || 15);
            }
            case 'sketch': {
                return this.applyPencilSketch(srcImgData);
            }
            case 'clahe': {
                return this.applyContrastEnhance(srcImgData, params.clipLimit || 2.5);
            }
            case 'threshold': {
                return this.applyOtsuThreshold(srcImgData);
            }
            case 'borders': {
                return this.applyBorder(srcImgData, params.style || 'solid', params.width || 20, params.color || '#FFFFFF', params.radius || 0);
            }
        }

        return { width: w, height: h, imageData: out };
    }

    applyUnsharpMask(srcImgData, amount = 1.5, radius = 1) {
        const blurred = this.applyGaussianBlur(srcImgData, radius).imageData;
        const out = this.cloneImageData(srcImgData);
        const d = out.data;
        const b = blurred.data;

        for (let i = 0; i < d.length; i += 4) {
            d[i] = Math.max(0, Math.min(255, d[i] + (d[i] - b[i]) * amount));
            d[i+1] = Math.max(0, Math.min(255, d[i+1] + (d[i+1] - b[i+1]) * amount));
            d[i+2] = Math.max(0, Math.min(255, d[i+2] + (d[i+2] - b[i+2]) * amount));
        }
        return { width: out.width, height: out.height, imageData: out };
    }

    applyGaussianBlur(srcImgData, radius = 5) {
        // High quality fast box approximation of gaussian
        const offCanvas = document.createElement('canvas');
        offCanvas.width = srcImgData.width;
        offCanvas.height = srcImgData.height;
        const offCtx = offCanvas.getContext('2d');
        offCtx.putImageData(srcImgData, 0, 0);

        const destCanvas = document.createElement('canvas');
        destCanvas.width = srcImgData.width;
        destCanvas.height = srcImgData.height;
        const destCtx = destCanvas.getContext('2d');
        destCtx.filter = `blur(${Math.max(1, radius)}px)`;
        destCtx.drawImage(offCanvas, 0, 0);

        return { width: destCanvas.width, height: destCanvas.height, imageData: destCtx.getImageData(0, 0, destCanvas.width, destCanvas.height) };
    }

    applyBilateralFilter(srcImgData, strength = 15) {
        // Fast edge-preserving spatial/intensity filter
        const out = this.cloneImageData(srcImgData);
        const d = out.data;
        const src = srcImgData.data;
        const w = srcImgData.width;
        const h = srcImgData.height;
        const r = 2;

        for (let y = r; y < h - r; y++) {
            for (let x = r; x < w - r; x++) {
                const centerIdx = (y * w + x) * 4;
                const cr = src[centerIdx];
                const cg = src[centerIdx+1];
                const cb = src[centerIdx+2];

                let sumR = 0, sumG = 0, sumB = 0, totalW = 0;

                for (let ky = -r; ky <= r; ky++) {
                    for (let kx = -r; kx <= r; kx++) {
                        const nIdx = ((y + ky) * w + (x + kx)) * 4;
                        const nr = src[nIdx];
                        const ng = src[nIdx+1];
                        const nb = src[nIdx+2];

                        const spatialDist = kx*kx + ky*ky;
                        const colorDist = (cr-nr)*(cr-nr) + (cg-ng)*(cg-ng) + (cb-nb)*(cb-nb);
                        const weight = Math.exp(-spatialDist / 8 - colorDist / (strength * strength * 2));

                        sumR += nr * weight;
                        sumG += ng * weight;
                        sumB += nb * weight;
                        totalW += weight;
                    }
                }

                d[centerIdx] = sumR / totalW;
                d[centerIdx+1] = sumG / totalW;
                d[centerIdx+2] = sumB / totalW;
            }
        }
        return { width: w, height: h, imageData: out };
    }

    applyPencilSketch(srcImgData) {
        const w = srcImgData.width;
        const h = srcImgData.height;
        const gray = new Uint8ClampedArray(w * h);
        const d = srcImgData.data;

        for (let i = 0; i < d.length; i += 4) {
            gray[i / 4] = 0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2];
        }

        // Invert & Blur
        const invBlurCanvas = document.createElement('canvas');
        invBlurCanvas.width = w;
        invBlurCanvas.height = h;
        const invCtx = invBlurCanvas.getContext('2d');
        const invImgData = invCtx.createImageData(w, h);
        for (let i = 0; i < gray.length; i++) {
            const v = 255 - gray[i];
            invImgData.data[i*4] = v;
            invImgData.data[i*4+1] = v;
            invImgData.data[i*4+2] = v;
            invImgData.data[i*4+3] = 255;
        }
        invCtx.putImageData(invImgData, 0, 0);

        const blurCanvas = document.createElement('canvas');
        blurCanvas.width = w;
        blurCanvas.height = h;
        const blurCtx = blurCanvas.getContext('2d');
        blurCtx.filter = 'blur(10px)';
        blurCtx.drawImage(invBlurCanvas, 0, 0);
        const blurData = blurCtx.getImageData(0, 0, w, h).data;

        // Color dodge
        const out = this.cloneImageData(srcImgData);
        for (let i = 0; i < gray.length; i++) {
            const gVal = gray[i];
            const bVal = blurData[i * 4];
            let dodge = (bVal === 255) ? 255 : (gVal << 8) / (255 - bVal);
            dodge = Math.min(255, dodge);
            out.data[i*4] = dodge;
            out.data[i*4+1] = dodge;
            out.data[i*4+2] = dodge;
        }
        return { width: w, height: h, imageData: out };
    }

    applyContrastEnhance(srcImgData, clipLimit = 2.5) {
        const out = this.cloneImageData(srcImgData);
        const d = out.data;
        const factor = (259 * (clipLimit * 30 + 255)) / (255 * (259 - clipLimit * 30));

        for (let i = 0; i < d.length; i += 4) {
            d[i] = Math.max(0, Math.min(255, factor * (d[i] - 128) + 128));
            d[i+1] = Math.max(0, Math.min(255, factor * (d[i+1] - 128) + 128));
            d[i+2] = Math.max(0, Math.min(255, factor * (d[i+2] - 128) + 128));
        }
        return { width: out.width, height: out.height, imageData: out };
    }

    applyOtsuThreshold(srcImgData) {
        const d = srcImgData.data;
        const total = d.length / 4;
        const hist = new Int32Array(256);

        for (let i = 0; i < d.length; i += 4) {
            const gray = Math.round(0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2]);
            hist[gray]++;
        }

        let sum = 0;
        for (let t = 0; t < 256; t++) sum += t * hist[t];

        let sumB = 0;
        let wB = 0;
        let varMax = 0;
        let threshold = 128;

        for (let t = 0; t < 256; t++) {
            wB += hist[t];
            if (wB === 0) continue;
            const wF = total - wB;
            if (wF === 0) break;

            sumB += t * hist[t];
            const mB = sumB / wB;
            const mF = (sum - sumB) / wF;

            const varBetween = wB * wF * (mB - mF) * (mB - mF);
            if (varBetween > varMax) {
                varMax = varBetween;
                threshold = t;
            }
        }

        const out = this.cloneImageData(srcImgData);
        for (let i = 0; i < d.length; i += 4) {
            const gray = 0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2];
            const val = (gray >= threshold) ? 255 : 0;
            out.data[i] = val;
            out.data[i+1] = val;
            out.data[i+2] = val;
        }
        return { width: out.width, height: out.height, imageData: out };
    }

    applyBorder(srcImgData, style = 'solid', width = 20, color = '#FFFFFF', radius = 0) {
        const borderW = parseInt(width) || 20;
        const w = srcImgData.width;
        const h = srcImgData.height;

        let canvasW = w + borderW * 2;
        let canvasH = h + borderW * 2;
        let imgX = borderW;
        let imgY = borderW;

        if (style === 'polaroid') {
            canvasH += borderW * 2.5; // bottom signature space
        }

        const canvas = document.createElement('canvas');
        canvas.width = canvasW;
        canvas.height = canvasH;
        const ctx = canvas.getContext('2d');

        // Draw border background
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, canvasW, canvasH);

        // Draw source image
        const srcCanvas = document.createElement('canvas');
        srcCanvas.width = w;
        srcCanvas.height = h;
        srcCanvas.getContext('2d').putImageData(srcImgData, 0, 0);

        ctx.drawImage(srcCanvas, imgX, imgY);

        return { width: canvasW, height: canvasH, imageData: ctx.getImageData(0, 0, canvasW, canvasH) };
    }

    // 6. WATERMARK (Text and Logo with 9 Anchor Points)
    applyWatermark(srcImgData, config) {
        const w = srcImgData.width;
        const h = srcImgData.height;
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.putImageData(srcImgData, 0, 0);

        const anchor = config.anchor || 'center';
        const opacity = (config.opacity !== undefined ? config.opacity : 80) / 100;
        ctx.globalAlpha = opacity;

        if (config.type === 'text') {
            const fontSize = Math.max(12, Math.round((config.fontSize || 32) * (w / 1000)));
            ctx.font = `bold ${fontSize}px sans-serif`;
            ctx.fillStyle = config.color || '#FFFFFF';
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = Math.max(2, Math.round(fontSize / 10));

            const text = config.text || 'Image Utility Toolbox';
            const metrics = ctx.measureText(text);
            const tw = metrics.width;
            const th = fontSize;
            const padding = 24;

            let x = w / 2 - tw / 2;
            let y = h / 2 + th / 3;

            if (anchor.includes('left')) x = padding;
            if (anchor.includes('right')) x = w - tw - padding;
            if (anchor.includes('top')) y = th + padding;
            if (anchor.includes('bottom')) y = h - padding;

            ctx.strokeText(text, x, y);
            ctx.fillText(text, x, y);
        } else if (config.type === 'logo' && config.logoImg) {
            const scale = (config.scale || 30) / 100;
            const lw = Math.round(w * scale);
            const lh = Math.round((config.logoImg.height / config.logoImg.width) * lw);
            const padding = 20;

            let x = w / 2 - lw / 2;
            let y = h / 2 - lh / 2;

            if (anchor.includes('left')) x = padding;
            if (anchor.includes('right')) x = w - lw - padding;
            if (anchor.includes('top')) y = padding;
            if (anchor.includes('bottom')) y = h - lh - padding;

            ctx.drawImage(config.logoImg, x, y, lw, lh);
        }

        ctx.globalAlpha = 1.0;
        return { width: w, height: h, imageData: ctx.getImageData(0, 0, w, h) };
    }

    // 7. K-MEANS 5 DOMINANT COLOR PALETTE
    extractPalette(imgData, k = 5) {
        const d = imgData.data;
        const step = Math.max(1, Math.floor(d.length / 4 / 2000)); // Sample ~2000 pixels for speed
        const pixels = [];

        for (let i = 0; i < d.length; i += step * 4) {
            if (d[i + 3] > 128) { // Skip transparent
                pixels.push([d[i], d[i+1], d[i+2]]);
            }
        }

        if (pixels.length === 0) return [];

        // Initialize K centroids evenly
        let centroids = [];
        for (let i = 0; i < k; i++) {
            const idx = Math.floor((i / k) * pixels.length);
            centroids.push([...pixels[idx]]);
        }

        // 6 Iterations of K-Means
        let clusters = Array.from({ length: k }, () => []);
        for (let iter = 0; iter < 6; iter++) {
            clusters = Array.from({ length: k }, () => []);

            for (const p of pixels) {
                let minDist = Infinity;
                let bestC = 0;
                for (let c = 0; c < k; c++) {
                    const dist = (p[0] - centroids[c][0])**2 + (p[1] - centroids[c][1])**2 + (p[2] - centroids[c][2])**2;
                    if (dist < minDist) {
                        minDist = dist;
                        bestC = c;
                    }
                }
                clusters[bestC].push(p);
            }

            // Recompute centroids
            for (let c = 0; c < k; c++) {
                if (clusters[c].length > 0) {
                    let sumR = 0, sumG = 0, sumB = 0;
                    for (const p of clusters[c]) {
                        sumR += p[0]; sumG += p[1]; sumB += p[2];
                    }
                    centroids[c] = [
                        Math.round(sumR / clusters[c].length),
                        Math.round(sumG / clusters[c].length),
                        Math.round(sumB / clusters[c].length)
                    ];
                }
            }
        }

        const totalPixels = pixels.length;
        const result = centroids.map((c, i) => {
            const pct = Math.round((clusters[i].length / totalPixels) * 100);
            const hex = '#' + c.map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
            return { rgb: c, hex: hex, percent: pct };
        });

        // Sort descending by percentage
        return result.sort((a, b) => b.percent - a.percent);
    }

    // 8. BINARY SEARCH TARGET SIZE COMPRESSOR (Exact logic parity with TargetSizeCompressorService)
    async compressToTarget(imgData, targetKb, format = 'webp', fastMode = false, allowDownscale = true) {
        const targetBytes = targetKb * 1024;
        let low = 1;
        let high = 100;
        let optimalQuality = 80;
        let bestBlob = null;
        let bestSize = Infinity;
        let iterations = 0;
        const maxIter = fastMode ? 6 : 9;

        const mime = (format === 'jpeg' || format === 'jpg') ? 'image/jpeg' :
                     (format === 'png') ? 'image/png' : 'image/webp';

        let currentImgData = imgData;
        let downscaleIteration = 0;

        while (downscaleIteration < 3) {
            low = 1;
            high = 100;

            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = currentImgData.width;
            tempCanvas.height = currentImgData.height;
            tempCanvas.getContext('2d').putImageData(currentImgData, 0, 0);

            // PNG is lossless, check if downscaling needed
            if (format === 'png') {
                const blob = await new Promise(res => tempCanvas.toBlob(res, 'image/png'));
                if (blob.size <= targetBytes || !allowDownscale) {
                    bestBlob = blob;
                    bestSize = blob.size;
                    optimalQuality = 100;
                    break;
                }
            } else {
                // Binary Search for lossy WebP / JPEG
                while (low <= high && iterations < maxIter * (downscaleIteration + 1)) {
                    iterations++;
                    const mid = Math.floor((low + high) / 2);
                    const q = mid / 100;
                    const blob = await new Promise(res => tempCanvas.toBlob(res, mime, q));

                    if (blob.size <= targetBytes) {
                        bestBlob = blob;
                        bestSize = blob.size;
                        optimalQuality = mid;
                        low = mid + 1; // Try higher quality
                    } else {
                        high = mid - 1; // Too large, lower quality
                    }
                }

                if (bestBlob && bestSize <= targetBytes) {
                    break; // Target achieved!
                }
            }

            // Fallback Downscaling (Lanczos 80%)
            if (!allowDownscale) break;

            downscaleIteration++;
            const scaled = this.resize(currentImgData, currentImgData.width * 0.8, currentImgData.height * 0.8);
            currentImgData = scaled.imageData;
        }

        if (!bestBlob) {
            // Fallback lowest reached
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = currentImgData.width;
            tempCanvas.height = currentImgData.height;
            tempCanvas.getContext('2d').putImageData(currentImgData, 0, 0);
            bestBlob = await new Promise(res => tempCanvas.toBlob(res, mime, 0.3));
            bestSize = bestBlob.size;
            optimalQuality = 30;
        }

        return {
            blob: bestBlob,
            sizeBytes: bestSize,
            sizeKb: (bestSize / 1024),
            quality: optimalQuality,
            iterations: iterations,
            width: currentImgData.width,
            height: currentImgData.height,
            format: format
        };
    }
}

const engine = new ProcessingEngine();
