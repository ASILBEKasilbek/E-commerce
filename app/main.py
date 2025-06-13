import cv2

# RTSP URL
rtsp_url = "rtsp://admin:Qwerty12@109.94.174.13:554/Streaming/Channels/102"

cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("RTSP manzil ochilmadi.")
else:
    print("RTSP oqim yuklandi. Video ko‘rsatilmoqda...")

# Video oqimini ko‘rsatish
while True:
    ret, frame = cap.read()
    if not ret:
        print("Kadrlardan birini o'qib bo'lmadi.")
        break

    # Oynada kadrni ko‘rsatish
    cv2.imshow("RTSP Video", frame)

    # Chiqarish uchun 'q' tugmasini bosing
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Oqimni to‘xtatish
cap.release()
cv2.destroyAllWindows()
