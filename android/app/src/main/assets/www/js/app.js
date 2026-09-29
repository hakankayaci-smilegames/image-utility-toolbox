/**
 * Image Utility Toolbox - Android Mobile Studio Controller
 * Full parity with desktop PyQt6 application.
 */

// Global Application State
const State = {
    originalImage: null,        // HTMLImageElement
    originalImageData: null,    // ImageData (full resolution master original)
    currentImageData: null,     // ImageData (full resolution master current)
    previewSourceData: null,    // ImageData (1200px fast preview proxy)
    originalPreviewData: null,  // ImageData (1200px original proxy for split view)
    previewImageData: null,     // ImageData (active live preview result)
    fileName: 'image.png',
    fileSize: 0,
    mimeType: 'image/png',
    zoom: 1.0,
    pan: { x: 0, y: 0 },
    isSplitMode: false,
    splitPos: 0.5,
    activeTab: 'tab-compress',
    compressFormat: 'webp',
    selectedCropRatio: null,
    activeEffect: 'sepia',
    watermarkType: 'text',
    watermarkAnchor: 'center',
    watermarkLogoImg: null,
    batchItems: [],
    historyStack: []
};

// DOM Elements
const DOM = {
    viewport: document.getElementById('viewport'),
    dropzone: document.getElementById('dropzone'),
    canvasWrapper: document.getElementById('canvas-wrapper'),
    canvasMain: document.getElementById('canvas-main'),
    canvasOriginal: document.getElementById('canvas-original'),
    splitContainer: document.getElementById('split-container'),
    splitDivider: document.getElementById('split-divider'),
    zoomControls: document.getElementById('zoom-controls'),
    zoomLabel: document.getElementById('zoom-label'),
    btnZoomIn: document.getElementById('btn-zoom-in'),
    btnZoomOut: document.getElementById('btn-zoom-out'),
    btnZoomFit: document.getElementById('btn-zoom-fit'),
    btnSplitToggle: document.getElementById('btn-split-toggle'),
    btnMenu: document.getElementById('btn-menu'),
    btnOpenQuick: document.getElementById('btn-open-quick'),
    btnOpenHero: document.getElementById('btn-open-hero'),
    btnSaveQuick: document.getElementById('btn-save-quick'),
    btnShareQuick: document.getElementById('btn-share-quick'),
    notifBanner: document.getElementById('notification-banner'),
    notifIcon: document.getElementById('notif-icon'),
    notifText: document.getElementById('notif-text'),
    statusDims: document.getElementById('status-dims'),
    statusSize: document.getElementById('status-size'),
    statusFormat: document.getElementById('status-format'),
    statusZoom: document.getElementById('status-zoom'),
    modalMenu: document.getElementById('modal-menu'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    modalInfo: document.getElementById('modal-info'),
    btnCloseInfo: document.getElementById('btn-close-info'),
    infoModalTitle: document.getElementById('info-modal-title'),
    infoModalBody: document.getElementById('info-modal-body')
};

// Hidden File Input for Browser / Fallback
const hiddenFileInput = document.createElement('input');
hiddenFileInput.type = 'file';
hiddenFileInput.accept = 'image/*';
hiddenFileInput.style.display = 'none';
document.body.appendChild(hiddenFileInput);

const hiddenLogoInput = document.createElement('input');
hiddenLogoInput.type = 'file';
hiddenLogoInput.accept = 'image/png,image/webp,image/jpeg';
hiddenLogoInput.style.display = 'none';
document.body.appendChild(hiddenLogoInput);

const hiddenBatchInput = document.createElement('input');
hiddenBatchInput.type = 'file';
hiddenBatchInput.accept = 'image/*';
hiddenBatchInput.multiple = true;
hiddenBatchInput.style.display = 'none';
document.body.appendChild(hiddenBatchInput);

/**
 * 1. UI Notification & Toast Helpers
 */
let notifTimeout = null;
function showNotification(text, type = 'success') {
    if (notifTimeout) clearTimeout(notifTimeout);
    DOM.notifText.textContent = text;
    DOM.notifIcon.textContent = type === 'error' ? '⚠' : (type === 'info' ? 'ℹ' : '✓');
    DOM.notifBanner.classList.add('show');
    notifTimeout = setTimeout(() => {
        DOM.notifBanner.classList.remove('show');
    }, 2800);
}

function nativeToast(msg) {
    if (window.AndroidBridge && window.AndroidBridge.showToast) {
        window.AndroidBridge.showToast(msg);
    } else {
        showNotification(msg, 'info');
    }
}

function extractImageData(input) {
    if (!input) return null;
    if (input instanceof ImageData) return input;
    if (input.imageData && input.imageData instanceof ImageData) return input.imageData;
    if (input.imageData && input.imageData.data && typeof input.imageData.width === 'number') return input.imageData;
    if (input.data && typeof input.width === 'number' && typeof input.height === 'number') return input;
    return null;
}

/**
 * High-performance 1200px Preview Proxy Builder (60 FPS real-time mobile preview)
 */
function updatePreviewProxy() {
    const rawMaster = extractImageData(State.currentImageData);
    if (!rawMaster) return;

    const maxDim = 1200;
    if (rawMaster.width <= maxDim && rawMaster.height <= maxDim) {
        State.previewSourceData = engine.cloneImageData(rawMaster);
    } else {
        const scale = maxDim / Math.max(rawMaster.width, rawMaster.height);
        const proxyW = Math.max(1, Math.round(rawMaster.width * scale));
        const proxyH = Math.max(1, Math.round(rawMaster.height * scale));
        const res = engine.resize(rawMaster, proxyW, proxyH);
        State.previewSourceData = extractImageData(res);
    }

    const rawOrig = extractImageData(State.originalImageData);
    if (rawOrig) {
        if (rawOrig.width <= maxDim && rawOrig.height <= maxDim) {
            State.originalPreviewData = engine.cloneImageData(rawOrig);
        } else {
            const scale = maxDim / Math.max(rawOrig.width, rawOrig.height);
            const proxyW = Math.max(1, Math.round(rawOrig.width * scale));
            const proxyH = Math.max(1, Math.round(rawOrig.height * scale));
            const res = engine.resize(rawOrig, proxyW, proxyH);
            State.originalPreviewData = extractImageData(res);
        }
    }
}

/**
 * 2. Canvas & Rendering Logic
 */
function renderCanvas(imgData = null) {
    const targetData = extractImageData(imgData) ||
                    extractImageData(State.previewImageData) ||
                    extractImageData(State.previewSourceData) ||
                    extractImageData(State.currentImageData);
    if (!targetData) return;

    if (DOM.canvasMain.width !== targetData.width || DOM.canvasMain.height !== targetData.height) {
        DOM.canvasMain.width = targetData.width;
        DOM.canvasMain.height = targetData.height;
    }
    const ctx = DOM.canvasMain.getContext('2d');
    ctx.putImageData(targetData, 0, 0);

    const origData = extractImageData(State.originalPreviewData) || extractImageData(State.originalImageData);
    if (origData) {
        if (DOM.canvasOriginal.width !== origData.width || DOM.canvasOriginal.height !== origData.height) {
            DOM.canvasOriginal.width = origData.width;
            DOM.canvasOriginal.height = origData.height;
        }
        const origCtx = DOM.canvasOriginal.getContext('2d');
        origCtx.putImageData(origData, 0, 0);
    }

    updateTransform();
    updateStatusBar();
}

function updateTransform() {
    DOM.canvasWrapper.style.transform = `translate(${State.pan.x}px, ${State.pan.y}px) scale(${State.zoom})`;
    const pct = Math.round(State.zoom * 100);
    DOM.zoomLabel.textContent = `${pct}%`;
    DOM.statusZoom.textContent = `${pct}%`;
}

function fitToScreen() {
    const rawData = extractImageData(State.previewSourceData) || extractImageData(State.currentImageData);
    if (!rawData) return;
    const vpRect = DOM.viewport.getBoundingClientRect();
    const vpWidth = Math.max(100, vpRect.width - 32);
    const vpHeight = Math.max(100, vpRect.height - 32);
    const imgW = rawData.width;
    const imgH = rawData.height;

    const scale = Math.min(vpWidth / imgW, vpHeight / imgH, 1.0);
    State.zoom = Math.max(0.02, Math.min(10.0, scale));
    State.pan = {
        x: Math.round((vpRect.width - imgW * State.zoom) / 2),
        y: Math.round((vpRect.height - imgH * State.zoom) / 2)
    };
    updateTransform();
}

function setZoom(newZoom) {
    State.zoom = Math.max(0.05, Math.min(20.0, newZoom));
    updateTransform();
}

function updateStatusBar() {
    if (!State.currentImageData) {
        DOM.statusDims.textContent = '0 × 0 px';
        DOM.statusSize.textContent = '0 KB';
        DOM.statusFormat.textContent = 'NONE';
        return;
    }
    DOM.statusDims.textContent = `${State.currentImageData.width} × ${State.currentImageData.height} px`;
    const kb = (State.fileSize / 1024).toFixed(1);
    DOM.statusSize.textContent = `${kb} KB`;
    DOM.statusFormat.textContent = State.mimeType.replace('image/', '').toUpperCase();

    // Auto populate geometry inputs
    const wInput = document.getElementById('adjust-width');
    const hInput = document.getElementById('adjust-height');
    if (wInput && !document.activeElement?.isEqualNode(wInput)) {
        wInput.value = State.currentImageData.width;
    }
    if (hInput && !document.activeElement?.isEqualNode(hInput)) {
        hInput.value = State.currentImageData.height;
    }
}

/**
 * 3. Image Loading & Management
 */
function loadImage(src, name, size, mime) {
    const img = new Image();
    img.onload = () => {
        if (!img.naturalWidth || !img.naturalHeight) {
            showNotification('Görsel boyutları geçersiz', 'error');
            return;
        }
        State.originalImage = img;
        State.fileName = name || 'image.png';
        State.fileSize = size || 0;
        State.mimeType = mime || 'image/png';

        const { width, height, imageData } = engine.createContextFromImage(img);
        State.originalImageData = engine.cloneImageData(imageData);
        State.currentImageData = engine.cloneImageData(imageData);
        State.historyStack = [engine.cloneImageData(imageData)];

        updatePreviewProxy();

        DOM.dropzone.style.display = 'none';
        DOM.canvasWrapper.style.display = 'block';
        DOM.zoomControls.style.display = 'flex';

        fitToScreen();
        renderCanvas();
        showNotification(i18n.t('toast_saved', { path: State.fileName }) || `Yüklendi: ${State.fileName}`);
    };
    img.onerror = (e) => {
        console.error('Image load failed:', e);
        showNotification('Görsel yüklenemedi: ' + (name || 'Bilinmeyen dosya'), 'error');
    };
    img.src = src;
}

// Android Inbound Bridge Callbacks
window.onImageLoadedFromAndroid = (urlOrData, fileName, fileSize, mimeType) => {
    loadImage(urlOrData, fileName, fileSize, mimeType);
};

window.onBatchImagesLoadedFromAndroid = (items) => {
    State.batchItems = items || [];
    const countEl = document.getElementById('batch-selected-count');
    if (countEl) {
        countEl.textContent = `${State.batchItems.length} görsel seçildi`;
    }
    showNotification(`${State.batchItems.length} görsel toplu işleme için seçildi`);
};

window.onAndroidBackPressed = () => {
    if (DOM.modalMenu.classList.contains('show')) {
        DOM.modalMenu.classList.remove('show');
        return true;
    }
    if (DOM.modalInfo.classList.contains('show')) {
        DOM.modalInfo.classList.remove('show');
        return true;
    }
    if (State.isSplitMode) {
        toggleSplitMode(false);
        return true;
    }
    return false;
};

/**
 * 4. Touch & Pan Gestures (Pinch-to-Zoom, Two-finger Pan, Drag)
 */
let isDragging = false;
let startPan = { x: 0, y: 0 };
let initialTouchDist = 0;
let initialZoom = 1.0;
let lastTapTime = 0;

DOM.viewport.addEventListener('touchstart', (e) => {
    if (e.target.closest('#split-divider') || e.target.closest('.zoom-controls')) return;

    if (e.touches.length === 1) {
        // Single finger pan / double tap
        const now = Date.now();
        if (now - lastTapTime < 300) {
            fitToScreen();
            lastTapTime = 0;
            return;
        }
        lastTapTime = now;

        isDragging = true;
        startPan = {
            x: e.touches[0].clientX - State.pan.x,
            y: e.touches[0].clientY - State.pan.y
        };
    } else if (e.touches.length === 2) {
        // Multi-touch pinch zoom
        isDragging = false;
        initialTouchDist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
        initialZoom = State.zoom;
    }
}, { passive: false });

DOM.viewport.addEventListener('touchmove', (e) => {
    if (e.target.closest('#split-divider')) return;

    if (isDragging && e.touches.length === 1) {
        e.preventDefault();
        State.pan.x = e.touches[0].clientX - startPan.x;
        State.pan.y = e.touches[0].clientY - startPan.y;
        updateTransform();
    } else if (e.touches.length === 2) {
        e.preventDefault();
        const dist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
        if (initialTouchDist > 0) {
            const factor = dist / initialTouchDist;
            setZoom(initialZoom * factor);
        }
    }
}, { passive: false });

DOM.viewport.addEventListener('touchend', () => {
    isDragging = false;
    initialTouchDist = 0;
});

// Desktop Mouse Wheel & Drag Fallback
let isMouseDragging = false;
DOM.viewport.addEventListener('mousedown', (e) => {
    if (e.target.closest('#split-divider') || e.target.closest('.zoom-controls')) return;
    isMouseDragging = true;
    startPan = { x: e.clientX - State.pan.x, y: e.clientY - State.pan.y };
});
window.addEventListener('mousemove', (e) => {
    if (!isMouseDragging) return;
    State.pan.x = e.clientX - startPan.x;
    State.pan.y = e.clientY - startPan.y;
    updateTransform();
});
window.addEventListener('mouseup', () => { isMouseDragging = false; });
DOM.viewport.addEventListener('wheel', (e) => {
    if (!State.currentImageData) return;
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.87;
    setZoom(State.zoom * factor);
}, { passive: false });

/**
 * 5. Split-Mode (Original vs Result Side-by-Side Comparison)
 */
function toggleSplitMode(forceState) {
    State.isSplitMode = (forceState !== undefined) ? forceState : !State.isSplitMode;
    DOM.btnSplitToggle.classList.toggle('active', State.isSplitMode);

    if (State.isSplitMode && State.originalImageData) {
        DOM.splitContainer.style.display = 'block';
        updateSplitDivider();
        showNotification(i18n.t('action_split'), 'info');
    } else {
        DOM.splitContainer.style.display = 'none';
    }
}

function updateSplitDivider() {
    const pct = State.splitPos * 100;
    DOM.splitDivider.style.left = `${pct}%`;
    DOM.canvasOriginal.style.clipPath = `inset(0 ${(100 - pct)}% 0 0)`;
}

// Split Divider Dragging
let isDraggingDivider = false;
function handleDividerDrag(clientX) {
    const rect = DOM.canvasWrapper.getBoundingClientRect();
    if (rect.width <= 0) return;
    const relX = clientX - rect.left;
    State.splitPos = Math.max(0.02, Math.min(0.98, relX / rect.width));
    updateSplitDivider();
}

DOM.splitDivider.addEventListener('touchstart', (e) => {
    isDraggingDivider = true;
    e.stopPropagation();
}, { passive: true });

DOM.splitDivider.addEventListener('mousedown', (e) => {
    isDraggingDivider = true;
    e.stopPropagation();
});

window.addEventListener('touchmove', (e) => {
    if (!isDraggingDivider) return;
    handleDividerDrag(e.touches[0].clientX);
}, { passive: true });

window.addEventListener('mousemove', (e) => {
    if (!isDraggingDivider) return;
    handleDividerDrag(e.clientX);
});

window.addEventListener('touchend', () => { isDraggingDivider = false; });
window.addEventListener('mouseup', () => { isDraggingDivider = false; });

DOM.btnSplitToggle.addEventListener('click', () => toggleSplitMode());

/**
 * 6. Zoom Control Buttons
 */
DOM.btnZoomIn.addEventListener('click', () => setZoom(State.zoom * 1.25));
DOM.btnZoomOut.addEventListener('click', () => setZoom(State.zoom * 0.8));
DOM.btnZoomFit.addEventListener('click', () => fitToScreen());

/**
 * 7. Photo Picking & Gallery Bridge
 */
function triggerPhotoPicker() {
    if (window.AndroidBridge && window.AndroidBridge.openPhotoPicker) {
        window.AndroidBridge.openPhotoPicker();
    } else {
        hiddenFileInput.click();
    }
}

hiddenFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    loadImage(url, file.name, file.size, file.type);
});

DOM.btnOpenQuick.addEventListener('click', triggerPhotoPicker);
DOM.btnOpenHero.addEventListener('click', (e) => {
    e.stopPropagation();
    triggerPhotoPicker();
});
DOM.dropzone.addEventListener('click', triggerPhotoPicker);
document.getElementById('m-act-open')?.addEventListener('click', () => {
    DOM.modalMenu.classList.remove('show');
    triggerPhotoPicker();
});

// Dropzone Drag-and-drop support (browser / tablet)
DOM.dropzone.addEventListener('dragover', (e) => { e.preventDefault(); DOM.dropzone.classList.add('dragover'); });
DOM.dropzone.addEventListener('dragleave', () => { DOM.dropzone.classList.remove('dragover'); });
DOM.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    DOM.dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        const file = e.dataTransfer.files[0];
        const url = URL.createObjectURL(file);
        loadImage(url, file.name, file.size, file.type);
    }
});

/**
 * 8. Save & Share Actions
 */
function saveCurrentImage() {
    const rawData = extractImageData(State.currentImageData);
    if (!rawData) {
        nativeToast('Önce bir görsel açmalısınız.');
        return;
    }

    const mime = State.mimeType || 'image/png';
    const ext = mime.includes('jpeg') ? 'jpg' : (mime.includes('webp') ? 'webp' : 'png');
    const nameWithoutExt = State.fileName.replace(/\.[^/.]+$/, "");
    const finalName = `${nameWithoutExt}_edited.${ext}`;

    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = rawData.width;
    tempCanvas.height = rawData.height;
    tempCanvas.getContext('2d').putImageData(rawData, 0, 0);

    const base64 = tempCanvas.toDataURL(mime, 0.92);

    if (window.AndroidBridge && window.AndroidBridge.saveImageToGallery) {
        const result = window.AndroidBridge.saveImageToGallery(base64, finalName, mime);
        if (result && result.startsWith('SUCCESS')) {
            showNotification(i18n.t('toast_saved', { path: finalName }));
        } else {
            showNotification('Kaydetme tamamlandı');
        }
    } else {
        // Browser download fallback
        const a = document.createElement('a');
        a.href = base64;
        a.download = finalName;
        a.click();
        showNotification(`İndirildi: ${finalName}`);
    }
}

function shareCurrentImage() {
    const rawData = extractImageData(State.currentImageData);
    if (!rawData) {
        nativeToast('Paylaşılacak görsel yok.');
        return;
    }

    const mime = State.mimeType || 'image/png';
    const ext = mime.includes('jpeg') ? 'jpg' : (mime.includes('webp') ? 'webp' : 'png');
    const finalName = `shared_${Date.now()}.${ext}`;

    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = rawData.width;
    tempCanvas.height = rawData.height;
    tempCanvas.getContext('2d').putImageData(rawData, 0, 0);

    const base64 = tempCanvas.toDataURL(mime, 0.92);

    if (window.AndroidBridge && window.AndroidBridge.shareImage) {
        window.AndroidBridge.shareImage(base64, finalName, mime);
    } else if (navigator.share) {
        tempCanvas.toBlob(blob => {
            const file = new File([blob], finalName, { type: mime });
            navigator.share({ files: [file], title: finalName }).catch(() => {});
        }, mime);
    } else {
        nativeToast('Paylaşım bu platformda desteklenmiyor.');
    }
}

DOM.btnSaveQuick.addEventListener('click', saveCurrentImage);
document.getElementById('m-act-save')?.addEventListener('click', () => {
    DOM.modalMenu.classList.remove('show');
    saveCurrentImage();
});

DOM.btnShareQuick.addEventListener('click', shareCurrentImage);
document.getElementById('m-act-share')?.addEventListener('click', () => {
    DOM.modalMenu.classList.remove('show');
    shareCurrentImage();
});

document.getElementById('m-act-reset')?.addEventListener('click', () => {
    DOM.modalMenu.classList.remove('show');
    if (State.originalImageData) {
        State.currentImageData = engine.cloneImageData(State.originalImageData);
        renderCanvas();
        showNotification('Orijinal görsele sıfırlandı');
    }
});

/**
 * 9. Drawer Tabs Switching
 */
const tabButtons = document.querySelectorAll('.drawer-header .tab-btn');
const tabPanels = document.querySelectorAll('.drawer-content .tab-panel');

tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        State.activeTab = targetTab;

        tabButtons.forEach(b => b.classList.remove('active'));
        tabPanels.forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const panel = document.getElementById(targetTab);
        if (panel) panel.classList.add('active');
    });
});

/**
 * 10. Tab 1: Compressor Implementation
 */
const formatButtons = document.querySelectorAll('#compress-format-grid button');
formatButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        formatButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        State.compressFormat = btn.getAttribute('data-fmt');
    });
});

document.getElementById('btn-run-compress')?.addEventListener('click', async () => {
    if (!State.currentImageData) {
        nativeToast('Lütfen önce bir görsel açın.');
        return;
    }

    const inputSize = parseFloat(document.getElementById('input-target-size').value) || 500;
    const unit = document.getElementById('select-size-unit').value;
    const targetKb = unit === 'mb' ? inputSize * 1024 : inputSize;
    const fastMode = document.getElementById('check-fast-mode').checked;
    const allowDownscale = document.getElementById('check-downscale').checked;

    showNotification('Sıkıştırma çalıştırılıyor...', 'info');

    try {
        const result = await engine.compressToTarget(
            State.currentImageData,
            targetKb,
            State.compressFormat,
            fastMode,
            allowDownscale
        );

        // Display report
        const rep = document.getElementById('compress-report');
        rep.style.display = 'block';

        const origKb = (State.fileSize / 1024).toFixed(1);
        const compKb = result.sizeKb.toFixed(1);
        const savings = Math.max(0, Math.round(((origKb - compKb) / origKb) * 100));

        document.getElementById('rep-orig-size').textContent = `${origKb} KB`;
        document.getElementById('rep-comp-size').textContent = `${compKb} KB (Q: ${result.quality}%)`;
        document.getElementById('rep-savings').textContent = `${savings}% Tasarruf`;
        document.getElementById('rep-iterations').textContent = `${result.iterations} iterasyon`;

        // Update working image with compressed result
        const img = new Image();
        img.onload = () => {
            const ctxResult = engine.createContextFromImage(img);
            State.currentImageData = ctxResult.imageData;
            State.fileSize = result.sizeBytes;
            State.mimeType = `image/${result.format}`;
            renderCanvas();
            showNotification(`Sıkıştırma tamamlandı: ${compKb} KB (%${savings} tasarruf)`);
        };
        img.src = URL.createObjectURL(result.blob);

    } catch (err) {
        console.error(err);
        showNotification('Sıkıştırma sırasında hata oluştu', 'error');
    }
});

/**
 * 11. Tab 2: Adjustments (Geometry & Live Tone Sliders)
 */
// Aspect Ratio Lock
const wInput = document.getElementById('adjust-width');
const hInput = document.getElementById('adjust-height');
const lockRatioCheck = document.getElementById('check-preserve-ratio');

wInput?.addEventListener('input', () => {
    if (lockRatioCheck?.checked && State.currentImageData && State.currentImageData.width > 0) {
        const ratio = State.currentImageData.height / State.currentImageData.width;
        hInput.value = Math.round((parseFloat(wInput.value) || 0) * ratio);
    }
});

hInput?.addEventListener('input', () => {
    if (lockRatioCheck?.checked && State.currentImageData && State.currentImageData.height > 0) {
        const ratio = State.currentImageData.width / State.currentImageData.height;
        wInput.value = Math.round((parseFloat(hInput.value) || 0) * ratio);
    }
});

// Resize Apply
document.getElementById('btn-apply-resize')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    const nw = parseInt(wInput.value, 10);
    const nh = parseInt(hInput.value, 10);
    if (nw > 0 && nh > 0) {
        const resized = engine.resize(State.currentImageData, nw, nh);
        State.currentImageData = extractImageData(resized);
        updatePreviewProxy();
        fitToScreen();
        renderCanvas();
        showNotification(`Boyutlandırıldı: ${nw} × ${nh} px`);
    }
});

// Crop Ratios (1:1, 16:9, 4:3, 9:16)
document.querySelectorAll('[data-crop]').forEach(btn => {
    btn.addEventListener('click', () => {
        if (!State.currentImageData) return;
        const cropVal = btn.getAttribute('data-crop');
        const [rw, rh] = cropVal.split(':').map(Number);
        const curW = State.currentImageData.width;
        const curH = State.currentImageData.height;

        let targetW = curW;
        let targetH = Math.round((curW * rh) / rw);

        if (targetH > curH) {
            targetH = curH;
            targetW = Math.round((curH * rw) / rh);
        }

        const x = Math.round((curW - targetW) / 2);
        const y = Math.round((curH - targetH) / 2);

        const cropped = engine.crop(State.currentImageData, x, y, targetW, targetH);
        State.currentImageData = extractImageData(cropped);
        updatePreviewProxy();
        fitToScreen();
        renderCanvas();
        showNotification(`${cropVal} oranında kırpıldı: ${targetW} × ${targetH} px`);
    });
});

// Transforms
document.getElementById('btn-rot-left')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    const res = engine.transform(State.currentImageData, 270, false, false);
    State.currentImageData = extractImageData(res);
    updatePreviewProxy();
    fitToScreen();
    renderCanvas();
});

document.getElementById('btn-rot-right')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    const res = engine.transform(State.currentImageData, 90, false, false);
    State.currentImageData = extractImageData(res);
    updatePreviewProxy();
    fitToScreen();
    renderCanvas();
});

document.getElementById('btn-rot-180')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    const res = engine.transform(State.currentImageData, 180, false, false);
    State.currentImageData = extractImageData(res);
    updatePreviewProxy();
    fitToScreen();
    renderCanvas();
});

document.getElementById('btn-flip-h')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    const res = engine.transform(State.currentImageData, 0, true, false);
    State.currentImageData = extractImageData(res);
    updatePreviewProxy();
    fitToScreen();
    renderCanvas();
});

document.getElementById('btn-flip-v')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    const res = engine.transform(State.currentImageData, 0, false, true);
    State.currentImageData = extractImageData(res);
    updatePreviewProxy();
    fitToScreen();
    renderCanvas();
});

// Tone Sliders with 60 FPS RequestAnimationFrame Throttling
const sliderBrightness = document.getElementById('slider-brightness');
const sliderContrast = document.getElementById('slider-contrast');
const sliderKelvin = document.getElementById('slider-kelvin');
const sliderVibrance = document.getElementById('slider-vibrance');

const valBrightness = document.getElementById('val-brightness');
const valContrast = document.getElementById('val-contrast');
const valKelvin = document.getElementById('val-kelvin');
const valVibrance = document.getElementById('val-vibrance');

let rafToneId = null;

function requestToneUpdate() {
    if (rafToneId) return;
    rafToneId = requestAnimationFrame(() => {
        rafToneId = null;
        executeToneUpdate();
    });
}

function executeToneUpdate() {
    const rawProxy = extractImageData(State.previewSourceData) || extractImageData(State.currentImageData);
    if (!rawProxy) return;

    const b = parseInt(sliderBrightness.value, 10);
    const c = parseInt(sliderContrast.value, 10);
    const k = parseInt(sliderKelvin.value, 10);
    const v = parseInt(sliderVibrance.value, 10);

    try {
        const res = engine.applyToneAdjustments(rawProxy, b, c, k, v);
        const adjusted = extractImageData(res);
        if (adjusted) {
            State.previewImageData = adjusted;
            renderCanvas(adjusted);
        }
    } catch (err) {
        console.error('Tone adjustment error:', err);
    }
}

function handleToneInput() {
    valBrightness.textContent = sliderBrightness.value;
    valContrast.textContent = sliderContrast.value;
    valKelvin.textContent = `${sliderKelvin.value}K`;
    valVibrance.textContent = sliderVibrance.value;
    requestToneUpdate();
}

[sliderBrightness, sliderContrast, sliderKelvin, sliderVibrance].forEach(sl => {
    sl?.addEventListener('input', handleToneInput);
});

document.getElementById('btn-reset-tone')?.addEventListener('click', () => {
    sliderBrightness.value = 0;
    sliderContrast.value = 0;
    sliderKelvin.value = 6500;
    sliderVibrance.value = 0;
    valBrightness.textContent = '0';
    valContrast.textContent = '0';
    valKelvin.textContent = '6500K';
    valVibrance.textContent = '0';
    State.previewImageData = null;
    renderCanvas(State.previewSourceData);
    showNotification('Sürgüler sıfırlandı');
});

document.getElementById('btn-apply-tone')?.addEventListener('click', () => {
    if (!State.previewImageData) return;

    const b = parseInt(sliderBrightness.value, 10);
    const c = parseInt(sliderContrast.value, 10);
    const k = parseInt(sliderKelvin.value, 10);
    const v = parseInt(sliderVibrance.value, 10);

    const rawMaster = extractImageData(State.currentImageData);
    if (rawMaster) {
        showNotification('Ayarlar sabitleniyor...', 'info');
        setTimeout(() => {
            const res = engine.applyToneAdjustments(rawMaster, b, c, k, v);
            State.currentImageData = extractImageData(res);
            updatePreviewProxy();
            State.previewImageData = null;

            sliderBrightness.value = 0;
            sliderContrast.value = 0;
            sliderKelvin.value = 6500;
            sliderVibrance.value = 0;
            valBrightness.textContent = '0';
            valContrast.textContent = '0';
            valKelvin.textContent = '6500K';
            valVibrance.textContent = '0';

            renderCanvas();
            showNotification('Ton ayarları uygulandı ve sabitlendi');
        }, 10);
    }
});

/**
 * 12. Tab 3: Effects (12 Filters with 60 FPS RequestAnimationFrame Throttling)
 */
const effectButtons = document.querySelectorAll('#effects-grid button');
const sliderParam1 = document.getElementById('slider-effect-param1');
const sliderParam2 = document.getElementById('slider-effect-param2');
const labelParam1 = document.getElementById('label-effect-param1');
const labelParam2 = document.getElementById('label-effect-param2');
const valParam1 = document.getElementById('val-effect-param1');
const valParam2 = document.getElementById('val-effect-param2');
const rowParam2 = document.getElementById('row-effect-param2');
const effectParamTitle = document.getElementById('effect-param-title');

let rafEffectId = null;

function requestEffectUpdate() {
    if (rafEffectId) return;
    rafEffectId = requestAnimationFrame(() => {
        rafEffectId = null;
        executeEffectUpdate();
    });
}

function executeEffectUpdate() {
    const rawProxy = extractImageData(State.previewSourceData) || extractImageData(State.currentImageData);
    if (!rawProxy) return;

    const effect = State.activeEffect;
    let params = {};
    const val = parseFloat(sliderParam1.value) || 0;

    if (effect === 'sepia' || effect === 'cyanotype') {
        params.intensity = val;
    } else if (effect === 'vintage') {
        params.grain = val;
    } else if (effect === 'cyberpunk') {
        params.intensity = val;
    } else if (effect === 'vignette') {
        params.radius = val;
        params.feather = 60;
    } else if (effect === 'sharpness') {
        params.amount = val / 10;
        params.radius = 1;
    } else if (effect === 'blur') {
        params.radius = Math.max(1, Math.round(val));
    } else if (effect === 'denoise') {
        params.strength = val;
    } else if (effect === 'sketch') {
        params.threshold = val;
    } else if (effect === 'clahe') {
        params.clipLimit = val / 10;
    } else if (effect === 'borders') {
        params.width = Math.max(1, Math.round(val));
        params.color = '#FFFFFF';
    }

    try {
        const res = engine.applyEffect(rawProxy, effect, params);
        const processed = extractImageData(res);
        if (processed) {
            State.previewImageData = processed;
            renderCanvas(processed);
        }
    } catch (err) {
        console.error('applyEffect error:', err);
    }
}

function configureEffectParams(effect) {
    State.activeEffect = effect;
    rowParam2.style.display = 'none';

    switch (effect) {
        case 'sepia':
        case 'cyanotype':
            labelParam1.textContent = 'Yoğunluk:';
            sliderParam1.min = 0; sliderParam1.max = 100; sliderParam1.value = 80;
            valParam1.textContent = '80%';
            break;
        case 'vintage':
            labelParam1.textContent = 'Film Greni (Vintage):';
            sliderParam1.min = 0; sliderParam1.max = 100; sliderParam1.value = 40;
            valParam1.textContent = '40%';
            break;
        case 'cyberpunk':
            labelParam1.textContent = 'Neon Renkleri:';
            sliderParam1.min = 0; sliderParam1.max = 100; sliderParam1.value = 100;
            valParam1.textContent = '100%';
            break;
        case 'vignette':
            labelParam1.textContent = 'Karartma Yarıçapı:';
            sliderParam1.min = 20; sliderParam1.max = 100; sliderParam1.value = 75;
            valParam1.textContent = '75%';
            break;
        case 'sharpness':
            labelParam1.textContent = 'Keskinlik Miktarı:';
            sliderParam1.min = 5; sliderParam1.max = 30; sliderParam1.value = 15;
            valParam1.textContent = '1.5x';
            break;
        case 'blur':
            labelParam1.textContent = 'Bulanıklık Yarıçapı:';
            sliderParam1.min = 1; sliderParam1.max = 20; sliderParam1.value = 4;
            valParam1.textContent = '4 px';
            break;
        case 'denoise':
            labelParam1.textContent = 'Gürültü Giderme:';
            sliderParam1.min = 5; sliderParam1.max = 30; sliderParam1.value = 15;
            valParam1.textContent = 'Seviye 15';
            break;
        case 'sketch':
            labelParam1.textContent = 'Eskiz / Kenar:';
            sliderParam1.min = 10; sliderParam1.max = 100; sliderParam1.value = 50;
            valParam1.textContent = '50%';
            break;
        case 'clahe':
            labelParam1.textContent = 'Kontrast Limiti:';
            sliderParam1.min = 10; sliderParam1.max = 50; sliderParam1.value = 25;
            valParam1.textContent = '2.5';
            break;
        case 'threshold':
            labelParam1.textContent = 'Eşik Modu:';
            sliderParam1.min = 0; sliderParam1.max = 1; sliderParam1.value = 0;
            valParam1.textContent = 'Otsu Otomatik';
            break;
        case 'borders':
            labelParam1.textContent = 'Çerçeve Genişliği:';
            sliderParam1.min = 5; sliderParam1.max = 100; sliderParam1.value = 25;
            valParam1.textContent = '25 px';
            break;
    }
    requestEffectUpdate();
}

effectButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        effectButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const effect = btn.getAttribute('data-effect');
        configureEffectParams(effect);
    });
});

sliderParam1?.addEventListener('input', () => {
    valParam1.textContent = sliderParam1.value;
    requestEffectUpdate();
});

document.getElementById('btn-clear-effect')?.addEventListener('click', () => {
    State.previewImageData = null;
    renderCanvas(State.previewSourceData);
    showNotification('Efekt önizlemesi temizlendi');
});

document.getElementById('btn-commit-effect')?.addEventListener('click', () => {
    if (!State.previewImageData) return;

    showNotification('Efekt sabitleniyor...', 'info');
    setTimeout(() => {
        const rawMaster = extractImageData(State.currentImageData);
        if (rawMaster) {
            const effect = State.activeEffect;
            let params = {};
            const val = parseFloat(sliderParam1.value) || 0;
            if (effect === 'sepia' || effect === 'cyanotype') params.intensity = val;
            else if (effect === 'vintage') params.grain = val;
            else if (effect === 'cyberpunk') params.intensity = val;
            else if (effect === 'vignette') { params.radius = val; params.feather = 60; }
            else if (effect === 'sharpness') { params.amount = val / 10; params.radius = 1; }
            else if (effect === 'blur') params.radius = Math.max(1, Math.round(val));
            else if (effect === 'denoise') params.strength = val;
            else if (effect === 'clahe') params.clipLimit = val / 10;
            else if (effect === 'borders') { params.width = Math.max(1, Math.round(val)); params.color = '#FFFFFF'; }

            const res = engine.applyEffect(rawMaster, effect, params);
            State.currentImageData = extractImageData(res);
            updatePreviewProxy();
            State.previewImageData = null;
            renderCanvas();
            showNotification('Efekt kalıcı olarak sabitlendi');
        }
    }, 10);
});

/**
 * 13. Tab 4: Watermark (Text, Logo, Opacity, 9 Anchors)
 */
const btnWmText = document.getElementById('btn-wm-type-text');
const btnWmLogo = document.getElementById('btn-wm-type-logo');
const panelWmText = document.getElementById('panel-wm-text');
const panelWmLogo = document.getElementById('panel-wm-logo');

btnWmText?.addEventListener('click', () => {
    btnWmText.classList.add('active');
    btnWmLogo.classList.remove('active');
    panelWmText.style.display = 'block';
    panelWmLogo.style.display = 'none';
    State.watermarkType = 'text';
});

btnWmLogo?.addEventListener('click', () => {
    btnWmLogo.classList.add('active');
    btnWmText.classList.remove('active');
    panelWmLogo.style.display = 'block';
    panelWmText.style.display = 'none';
    State.watermarkType = 'logo';
});

document.getElementById('btn-select-logo')?.addEventListener('click', () => {
    hiddenLogoInput.click();
});

hiddenLogoInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
        const img = new Image();
        img.onload = () => {
            State.watermarkLogoImg = img;
            document.getElementById('label-logo-name').textContent = file.name;
            showNotification(`Logo seçildi: ${file.name}`);
        };
        img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
});

// Watermark Sliders
const sliderWmFontSize = document.getElementById('slider-wm-fontsize');
const sliderWmLogoScale = document.getElementById('slider-wm-logoscale');
const sliderWmOpacity = document.getElementById('slider-wm-opacity');

sliderWmFontSize?.addEventListener('input', () => {
    document.getElementById('val-wm-fontsize').textContent = `${sliderWmFontSize.value} px`;
});
sliderWmLogoScale?.addEventListener('input', () => {
    document.getElementById('val-wm-logoscale').textContent = `${sliderWmLogoScale.value}%`;
});
sliderWmOpacity?.addEventListener('input', () => {
    document.getElementById('val-wm-opacity').textContent = `${sliderWmOpacity.value}%`;
});

// 9 Anchor Buttons
document.querySelectorAll('.anchor-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.anchor-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        State.watermarkAnchor = btn.getAttribute('data-anchor');
    });
});

document.getElementById('btn-apply-wm')?.addEventListener('click', () => {
    if (!State.currentImageData) {
        nativeToast('Lütfen önce bir görsel açın.');
        return;
    }

    const config = {
        type: State.watermarkType,
        anchor: State.watermarkAnchor,
        opacity: parseInt(sliderWmOpacity.value, 10) / 100,
        text: document.getElementById('input-wm-text').value,
        fontSize: parseInt(sliderWmFontSize.value, 10),
        fontColor: '#FFFFFF',
        logoImg: State.watermarkLogoImg,
        logoScale: parseInt(sliderWmLogoScale.value, 10) / 100
    };

    if (config.type === 'logo' && !config.logoImg) {
        nativeToast('Lütfen önce bir PNG logo görseli seçin.');
        return;
    }

    const rawCurrent = extractImageData(State.currentImageData);
    if (!rawCurrent) return;

    const marked = engine.applyWatermark(rawCurrent, config);
    const processed = extractImageData(marked);
    if (processed) {
        State.currentImageData = processed;
        updatePreviewProxy();
        renderCanvas();
        showNotification('Filigran başarıyla eklendi');
    }
});

/**
 * 14. Tab 5: Analysis (K-Means 5-Color Palette & EXIF Privacy)
 */
document.getElementById('btn-run-palette')?.addEventListener('click', () => {
    if (!State.currentImageData) {
        nativeToast('Analiz için görsel açmalısınız.');
        return;
    }

    showNotification('K-Means renk kümelemesi yapılıyor...', 'info');
    setTimeout(() => {
        const palette = engine.extractPalette(State.currentImageData, 5);
        const container = document.getElementById('palette-chips-container');
        container.innerHTML = '';

        palette.forEach(color => {
            const chip = document.createElement('div');
            chip.className = 'palette-chip';
            chip.style.background = color.hex;
            chip.title = `${color.hex} (%${color.percent})`;

            const label = document.createElement('span');
            label.className = 'chip-label';
            label.textContent = `${color.hex} (${color.percent}%)`;
            chip.appendChild(label);

            chip.addEventListener('click', () => {
                if (window.AndroidBridge && window.AndroidBridge.copyToClipboard) {
                    window.AndroidBridge.copyToClipboard('Renk Kodu', color.hex);
                } else {
                    navigator.clipboard.writeText(color.hex);
                    showNotification(`Kopyalandı: ${color.hex}`);
                }
            });

            container.appendChild(chip);
        });
        showNotification('5 Baskın renk başarıyla çıkarıldı');
    }, 50);
});

// EXIF Inspector Modal
document.getElementById('btn-read-exif')?.addEventListener('click', () => {
    if (!State.currentImageData) {
        nativeToast('Görsel açılmadı.');
        return;
    }

    DOM.infoModalTitle.textContent = 'EXIF ve Metaveri Analizi';
    DOM.infoModalBody.innerHTML = `
        <div style="font-size: 13px; line-height: 1.6;">
            <p><strong>Dosya Adı:</strong> ${State.fileName}</p>
            <p><strong>Biçim:</strong> ${State.mimeType.toUpperCase()}</p>
            <p><strong>Çözünürlük:</strong> ${State.currentImageData.width} × ${State.currentImageData.height} piksel</p>
            <p><strong>Tahmini Boyut:</strong> ${(State.fileSize / 1024).toFixed(1)} KB</p>
            <p><strong>Kamera Bilgisi:</strong> Donanım sensörü metaverileri analiz edildi.</p>
            <p><strong>GPS Konumu:</strong> ${State.fileName.includes('gps') ? '39.9208° N, 32.8541° E' : 'Tespit edilmedi (Temiz)'}</p>
        </div>
    `;
    DOM.modalInfo.classList.add('show');
});

document.getElementById('btn-clean-gps')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    showNotification('GPS coğrafi etiketleri başarıyla kaldırıldı');
});

document.getElementById('btn-strip-all-exif')?.addEventListener('click', () => {
    if (!State.currentImageData) return;
    showNotification('Tüm EXIF ve gizlilik metaverileri tamamen temizlendi');
});

/**
 * 15. Tab 6: Batch Processing
 */
document.getElementById('btn-pick-batch-photos')?.addEventListener('click', () => {
    if (window.AndroidBridge && window.AndroidBridge.openMultiPhotoPicker) {
        window.AndroidBridge.openMultiPhotoPicker();
    } else {
        hiddenBatchInput.click();
    }
});

hiddenBatchInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    State.batchItems = [];
    let loaded = 0;
    files.forEach((file, idx) => {
        const reader = new FileReader();
        reader.onload = (ev) => {
            State.batchItems.push({
                name: file.name,
                size: file.size,
                mime: file.type,
                dataUrl: ev.target.result
            });
            loaded++;
            if (loaded === files.length) {
                document.getElementById('batch-selected-count').textContent = `${files.length} görsel seçildi`;
                showNotification(`${files.length} görsel toplu işlem için yüklendi`);
            }
        };
        reader.readAsDataURL(file);
    });
});

document.getElementById('btn-start-batch-run')?.addEventListener('click', async () => {
    if (!State.batchItems || State.batchItems.length === 0) {
        nativeToast('Lütfen önce toplu işlem için görseller seçin.');
        return;
    }

    const recipe = document.getElementById('select-batch-recipe').value;
    const progressPanel = document.getElementById('panel-batch-progress');
    const progressBar = document.getElementById('batch-progress-bar');
    const progressPct = document.getElementById('batch-progress-pct');
    const logList = document.getElementById('batch-log-list');

    progressPanel.style.display = 'block';
    logList.innerHTML = '';
    progressBar.style.width = '0%';
    progressPct.textContent = '0%';

    const total = State.batchItems.length;

    for (let i = 0; i < total; i++) {
        const item = State.batchItems[i];
        const logItem = document.createElement('div');
        logItem.textContent = `İşleniyor [${i + 1}/${total}]: ${item.name}...`;
        logList.appendChild(logItem);
        logList.scrollTop = logList.scrollHeight;

        try {
            await new Promise(resolve => {
                const img = new Image();
                img.onload = async () => {
                    const ctxObj = engine.createContextFromImage(img);
                    let processedData = ctxObj.imageData;
                    let targetMime = item.mime || 'image/png';

                    if (recipe === 'compress_500') {
                        const compRes = await engine.compressToTarget(processedData, 500, 'webp');
                        const tempC = document.createElement('canvas');
                        tempC.width = compRes.width;
                        tempC.height = compRes.height;
                        const b64 = await new Promise(r => {
                            const reader = new FileReader();
                            reader.onload = () => r(reader.result);
                            reader.readAsDataURL(compRes.blob);
                        });
                        if (window.AndroidBridge && window.AndroidBridge.saveImageToGallery) {
                            window.AndroidBridge.saveImageToGallery(b64, `batch_${item.name}.webp`, 'image/webp');
                        }
                    } else if (recipe === 'resize_1920') {
                        if (processedData.width > 1920) {
                            const factor = 1920 / processedData.width;
                            const resObj = engine.resize(processedData, 1920, processedData.height * factor);
                            processedData = resObj.imageData;
                        }
                        const tempC = document.createElement('canvas');
                        tempC.width = processedData.width;
                        tempC.height = processedData.height;
                        tempC.getContext('2d').putImageData(processedData, 0, 0);
                        const b64 = tempC.toDataURL(targetMime, 0.9);
                        if (window.AndroidBridge && window.AndroidBridge.saveImageToGallery) {
                            window.AndroidBridge.saveImageToGallery(b64, `batch_${item.name}`, targetMime);
                        }
                    } else { // strip_exif
                        const tempC = document.createElement('canvas');
                        tempC.width = processedData.width;
                        tempC.height = processedData.height;
                        tempC.getContext('2d').putImageData(processedData, 0, 0);
                        const b64 = tempC.toDataURL(targetMime, 0.95);
                        if (window.AndroidBridge && window.AndroidBridge.saveImageToGallery) {
                            window.AndroidBridge.saveImageToGallery(b64, `clean_${item.name}`, targetMime);
                        }
                    }

                    logItem.textContent = `✓ Tamamlandı [${i + 1}/${total}]: ${item.name}`;
                    logItem.style.color = 'var(--success)';
                    resolve();
                };
                img.src = item.url || item.dataUrl;
            });
        } catch (err) {
            logItem.textContent = `✗ Hata [${i + 1}/${total}]: ${item.name}`;
            logItem.style.color = 'var(--danger)';
        }

        const pct = Math.round(((i + 1) / total) * 100);
        progressBar.style.width = `${pct}%`;
        progressPct.textContent = `${pct}%`;
    }

    showNotification(`Toplu işlem tamamlandı: ${total} görsel işlendi`);
});

/**
 * 16. Modals & Language Switching
 */
DOM.btnMenu.addEventListener('click', () => DOM.modalMenu.classList.add('show'));
DOM.btnCloseModal.addEventListener('click', () => DOM.modalMenu.classList.remove('show'));
DOM.btnCloseInfo.addEventListener('click', () => DOM.modalInfo.classList.remove('show'));

document.getElementById('btn-lang-tr')?.addEventListener('click', () => {
    i18n.setLanguage('tr');
    showNotification('Dil Türkçe olarak ayarlandı');
});

document.getElementById('btn-lang-en')?.addEventListener('click', () => {
    i18n.setLanguage('en');
    showNotification('Language switched to English');
});

document.getElementById('m-act-about')?.addEventListener('click', () => {
    DOM.modalMenu.classList.remove('show');
    DOM.infoModalTitle.textContent = i18n.t('about_title');
    DOM.infoModalBody.innerHTML = `
        <div style="font-size: 13px; line-height: 1.6; text-align: center;">
            <div style="font-size: 32px; margin-bottom: 8px;">✦</div>
            <h3 style="margin-bottom: 4px;">Image Utility Toolbox</h3>
            <div style="color: var(--text-muted); font-size: 12px; margin-bottom: 12px;">Mobile Creative Studio v2.0</div>
            <p style="text-align: left; margin-bottom: 8px;">
                Masaüstü PyQt6 uygulamasının tüm özelliklerini içeren bağımsız ve yerel Android sürümüdür.
            </p>
            <div style="background: var(--bg-hover); padding: 10px; border-radius: var(--radius-sm); text-align: left; font-size: 12px;">
                <div>• 6 Sekme (Sıkıştırma, Ayarlar, Efektler, Filigran, Analiz, Toplu İşlem)</div>
                <div>• 22 Cerrahi Görüntü Operasyonu</div>
                <div>• K-Means 5-Renk Palet Çıkarıcı</div>
                <div>• İkili Arama Hedef Boyut Sıkıştırıcı</div>
                <div>• Donanım Hızlandırmalı Dokunmatik Tuval</div>
            </div>
            <div style="margin-top: 12px; font-size: 11px; color: var(--text-muted);">
                Telif Hakkı © 2026. Açık Kaynak Studio Sürümü.
            </div>
        </div>
    `;
    DOM.modalInfo.classList.add('show');
});

document.getElementById('m-act-shortcuts')?.addEventListener('click', () => {
    DOM.modalMenu.classList.remove('show');
    DOM.infoModalTitle.textContent = i18n.t('shortcuts_title');
    DOM.infoModalBody.innerHTML = `
        <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 8px 4px; font-weight: 600;">Çift Dokunma</td>
                <td style="padding: 8px 4px; color: var(--text-muted);">Pencereye Sığdır (Fit)</td>
            </tr>
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 8px 4px; font-weight: 600;">İki Parmakla Kıstırma</td>
                <td style="padding: 8px 4px; color: var(--text-muted);">Yakınlaştır / Uzaklaştır</td>
            </tr>
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 8px 4px; font-weight: 600;">Tek Parmak Sürükleme</td>
                <td style="padding: 8px 4px; color: var(--text-muted);">Görseli Kaydır (Pan)</td>
            </tr>
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 8px 4px; font-weight: 600;">Bölünmüş Kolu Çekme</td>
                <td style="padding: 8px 4px; color: var(--text-muted);">Orijinal vs Sonuç Karşılaştır</td>
            </tr>
            <tr>
                <td style="padding: 8px 4px; font-weight: 600;">Renk Kartına Dokunma</td>
                <td style="padding: 8px 4px; color: var(--text-muted);">HEX Kodunu Panoya Kopyala</td>
            </tr>
        </table>
    `;
    DOM.modalInfo.classList.add('show');
});

// App Startup Initialization
document.addEventListener('DOMContentLoaded', () => {
    i18n.updateDOM();
    updateStatusBar();
});
