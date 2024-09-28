'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from "../components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../components/ui/card"
import { Camera, Image, X, Send, Calendar, MapPin } from "lucide-react"
import { useEnv } from "../env/provider"

interface LocationData {
  latitude: number;
  longitude: number;
}

export function MobilePwaPhotoApp() {
  const env = useEnv();
  const apiUrl = (env as { API_URL?: string }).API_URL;

  const [photo, setPhoto] = useState<string | null>(null)
  const [cameraActive, setCameraActive] = useState(false)
  const [calendarData, setCalendarData] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [location, setLocation] = useState<LocationData | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const handleTakePhoto = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        streamRef.current = stream
        setCameraActive(true)
      }
    } catch (err) {
      console.error("Error accessing camera:", err)
      alert("Unable to access camera. Please check permissions.")
    }
  }

  const handleCapture = () => {
    if (videoRef.current) {
      const canvas = document.createElement('canvas')
      canvas.width = videoRef.current.videoWidth
      canvas.height = videoRef.current.videoHeight
      canvas.getContext('2d')?.drawImage(videoRef.current, 0, 0)
      const imageDataUrl = canvas.toDataURL('image/jpeg')
      setPhoto(imageDataUrl)
      setCameraActive(false)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      recordLocation()
    }
  }

  const recordLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          })
          console.log("Location recorded successfully")
        },
        (error) => {
          console.error("Error getting location:", error)
          alert("Unable to get your location. Please check permissions.")
        }
      )
    } else {
      console.error("Geolocation is not supported by this browser.")
      alert("Your device doesn't support geolocation.")
    }
  }

  const handleChoosePhoto = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setPhoto(reader.result as string)
        recordLocation()
      }
      reader.readAsDataURL(file)
    }
  }

  const handleClear = () => {
    setPhoto(null)
    setCalendarData(null)
    setLocation(null)
    setCameraActive(false)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
  }

  const handleSendPhoto = async () => {
    setLoading(true);
    try {
      const formData = new FormData()
      if (photo) {
        // Convert base64 to blob
        const response = await fetch(photo)
        const blob = await response.blob()
        formData.append('photo', blob, 'photo.jpg')
      }

      let url = `${apiUrl}/get_ics_card/`
      if (location) {
        url += `?latitude=${location.latitude}&longitude=${location.longitude}`
      }

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to process the image')
      }

      const calendarData = await response.text()
      setCalendarData(calendarData)
      console.log("Photo and location sent successfully")
    } catch (error) {
      console.error("Error sending photo:", error)
      alert("Failed to process the image. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCalendar = () => {
    if (calendarData) {
      const blob = new Blob([calendarData], { type: 'text/calendar' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'event.ics'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      console.log("Calendar event downloaded")
      alert("Calendar event downloaded. Please open it with your calendar application.")
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">Pic2Contact</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center space-y-4">
        {cameraActive ? (
          <video ref={videoRef} autoPlay className="w-64 h-64 object-cover rounded-lg" />
        ) : photo && !calendarData ? (
          <img src={photo} alt="Captured" className="w-64 h-64 object-cover rounded-lg" />
        ) : calendarData ? (
          <div className="w-64 h-64 bg-gray-100 rounded-lg p-4 overflow-auto">
            <pre className="text-xs whitespace-pre-wrap">{calendarData}</pre>
          </div>
        ) : (
          <div className="w-64 h-64 bg-gray-200 rounded-lg flex items-center justify-center">
            <Image className="w-16 h-16 text-gray-400" />
          </div>
        )}
        {loading && <p className="text-sm text-gray-500">Processing image...</p>}
        {location && (
          <p className="text-sm text-gray-500 flex items-center gap-1">
            <MapPin className="w-4 h-4" />
            Location: {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
          </p>
        )}
      </CardContent>
      <CardFooter className="flex flex-wrap justify-center gap-2">
        {photo || cameraActive ? (
          <>
            <Button variant="destructive" onClick={handleClear} className="flex items-center gap-2">
              <X className="w-4 h-4" />
              Clear
            </Button>
            {photo && !calendarData && (
              <Button 
                variant="default" 
                onClick={handleSendPhoto} 
                className="flex items-center gap-2"
                disabled={loading}
              >
                <Send className="w-4 h-4" />
                Send Photo
              </Button>
            )}
            {calendarData && (
              <Button 
                variant="default" 
                onClick={handleAddToCalendar} 
                className="flex items-center gap-2"
              >
                <Calendar className="w-4 h-4" />
                Add to Contacts
              </Button>
            )}
          </>
        ) : (
          <>
            <Button variant="outline" className="flex items-center gap-2">
              <label htmlFor="fileInput" className="cursor-pointer flex items-center gap-2">
                <Image className="w-4 h-4" />
                Choose Photo
              </label>
              <input
                id="fileInput"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleChoosePhoto}
              />
            </Button>
            <Button
              variant="default"
              className="flex items-center gap-2"
              onClick={cameraActive ? handleCapture : handleTakePhoto}
            >
              <Camera className="w-4 h-4" />
              {cameraActive ? 'Capture' : 'Take Photo'}
            </Button>
          </>
        )}
      </CardFooter>
    </Card>
  )
}