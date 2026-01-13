try:
    from ultralytics import YOLO
    _MODEL = None
    try:
        _MODEL = YOLO('yolov8n.pt')
    except Exception:
        _MODEL = None
except Exception:
    _MODEL = None

def detect(path, conf=0.25):
    """Run YOLOv8 detection if model is available, otherwise return a simulated detection.
    Returns a list of dicts: {'bbox':[x1,y1,x2,y2], 'confidence':float, 'label':str}
    """
    if _MODEL is not None:
        results = _MODEL.predict(source=path, conf=conf, verbose=False)
        r = results[0]
        detections = []
        try:
            boxes = r.boxes.xyxy.tolist()
            confs = r.boxes.conf.tolist()
            clsids = r.boxes.cls.tolist()
            names = r.names if hasattr(r, 'names') else {}
            for box, c, cid in zip(boxes, confs, clsids):
                label = names.get(int(cid), str(int(cid))) if isinstance(names, dict) else str(int(cid))
                detections.append({'bbox':[int(box[0]),int(box[1]),int(box[2]),int(box[3])], 'confidence':float(c), 'label':label})
        except Exception:
            pass
        return detections
    # fallback simulated detection
    return [{'bbox':[10,10,100,100],'confidence':0.88,'label':'zorro'}]
