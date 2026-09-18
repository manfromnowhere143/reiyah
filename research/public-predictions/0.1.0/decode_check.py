"""A small, separate CPU check of the frozen detection export's numeric steps.

Only batch-one, 640-square, FP32 COCO detection heads are in scope. This is a
development cross-check, not a general decoder or a substitute for the publisher.
"""
import numpy as np


def letterbox_input(bgr, cv2):
    """Independent construction for the fixed square/centered/linear policy."""
    if bgr.dtype != np.uint8 or bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError('Expected three-channel uint8 source pixels')
    height, width = bgr.shape[:2]
    scale = min(640 / height, 640 / width)
    resized_width, resized_height = round(width * scale), round(height * scale)
    horizontal, vertical = (640 - resized_width) / 2, (640 - resized_height) / 2
    pixels = cv2.resize(bgr, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)
    padded = cv2.copyMakeBorder(pixels, round(vertical - 0.1), round(vertical + 0.1),
                               round(horizontal - 0.1), round(horizontal + 0.1),
                               cv2.BORDER_CONSTANT, value=(114, 114, 114))
    return np.ascontiguousarray(padded[:, :, ::-1].transpose(2, 0, 1)[None]).astype(np.float32) / np.float32(255)


def decode(raw, *, end_to_end, width, height, confidence=0.25, nms_iou=0.7, maximum=300):
    """Decode retained raw head outputs without calling publisher NMS/box helpers."""
    value = np.array(raw, dtype=np.float32, copy=True)
    if value.ndim != 3 or value.shape[0] != 1 or not np.isfinite(value).all():
        raise ValueError('Finite batch-one raw output required')
    if end_to_end:
        if value.shape[2] != 6:
            raise ValueError('Expected [batch, candidates, xyxy+score+class]')
        detections = value[0][value[0, :, 4] > confidence][:maximum].copy()
    else:
        if value.shape[1] != 84 or value.shape[2] > 30000:
            raise ValueError('Expected bounded [batch, 4+80, candidates]')
        candidates = value[0].T
        classes = np.argmax(candidates[:, 4:], axis=1)
        scores = candidates[np.arange(len(candidates)), 4 + classes]
        chosen = np.flatnonzero(scores > confidence)
        candidates, classes, scores = candidates[chosen], classes[chosen], scores[chosen]
        centers, halves = candidates[:, :2], candidates[:, 2:4] / np.float32(2)
        rectangles = np.concatenate((centers - halves, centers + halves), axis=1)
        # Match the frozen publisher's FP32 class-offset arithmetic, including
        # its finite-precision geometry. This is not idealized real arithmetic.
        shifted = rectangles + classes[:, None].astype(np.float32) * np.float32(7680)
        size = shifted[:, 2:] - shifted[:, :2]
        areas = size[:, 0] * size[:, 1]
        order = np.argsort(-scores, kind='stable')
        kept = []
        while len(order) and len(kept) < maximum:
            current = int(order[0]); kept.append(current)
            remaining = order[1:]
            left = np.maximum(shifted[current, :2], shifted[remaining, :2])
            right = np.minimum(shifted[current, 2:], shifted[remaining, 2:])
            wh = np.maximum(np.float32(0), right - left)
            intersection = wh[:, 0] * wh[:, 1]
            overlap = intersection / (areas[current] + areas[remaining] - intersection)
            order = remaining[overlap <= nms_iou]
        detections = np.concatenate((rectangles[kept], scores[kept, None],
                                     classes[kept, None].astype(np.float32)), axis=1)
    if not len(detections):
        return np.zeros((0, 6), dtype=np.float32)
    gain = min(640 / height, 640 / width)
    xpad = round((640 - round(width * gain)) / 2 - 0.1)
    ypad = round((640 - round(height * gain)) / 2 - 0.1)
    detections[:, [0, 2]] -= xpad
    detections[:, [1, 3]] -= ypad
    detections[:, :4] /= gain
    detections[:, [0, 2]] = np.clip(detections[:, [0, 2]], 0, width)
    detections[:, [1, 3]] = np.clip(detections[:, [1, 3]], 0, height)
    return detections


def compare(expected, actual, *, coordinate_tolerance=0.0005):
    """Compare complete ordered outputs. No box matching or omissions hide a gap."""
    expected, actual = np.asarray(expected), np.asarray(actual)
    if expected.shape != actual.shape or expected.ndim != 2 or expected.shape[1] != 6:
        raise ValueError('Publisher and separate decoder output shapes differ')
    if not np.isfinite(expected).all() or not np.isfinite(actual).all():
        raise ValueError('Nonfinite decoded output')
    coordinate_error = float(np.max(np.abs(expected[:, :4] - actual[:, :4]))) if len(expected) else 0.0
    if not np.array_equal(expected[:, 4:], actual[:, 4:]) or coordinate_error > coordinate_tolerance:
        raise ValueError('Publisher and separate decoder values/order differ: ' + str(coordinate_error))
    return {'detections': len(expected), 'maximum_coordinate_error_pixels': coordinate_error,
            'coordinate_tolerance_pixels': coordinate_tolerance,
            'scores_and_classes_exact': True, 'order_equal': True}
