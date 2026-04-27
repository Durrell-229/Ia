/**
 * Gestionnaire de capture caméra pour les copies papier
 */
class CameraCapture {
    constructor(videoElementId) {
        this.video = document.getElementById(videoElementId);
        this.stream = null;
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: "environment",
                    width: { ideal: 4096 },
                    height: { ideal: 2160 }
                }
            });
            this.video.srcObject = this.stream;
        } catch (err) {
            console.error("Erreur accès caméra:", err);
            throw err;
        }
    }

    capture() {
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0);
        return canvas.toDataURL('image/jpeg', 0.9);
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}
