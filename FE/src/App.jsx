import { useState, useRef, useEffect } from 'react'
import logo from './assets/Group 11.svg'
import './App.css'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = 0
    }
  }, [])

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom()
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = { id: Date.now(), text: input, sender: 'user' }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    try {
     const res = await fetch('https://sudo-backend-kkpm.onrender.com/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      })
      const data = await res.json()
      const text = [data.greeting, data.answer, data.info, data.followup].filter(Boolean).join('\n')
      const aiMessage = { id: Date.now() + 1, text, sender: 'ai' }
      setMessages(prev => [...prev, aiMessage])
    } catch (e) {
      const errMessage = { id: Date.now() + 1, text: '서버 연결에 실패했습니다.', sender: 'ai' }
      setMessages(prev => [...prev, errMessage])
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  return (
    <div className="container">
      <img src={logo} alt="logo" className="logo" />
      <h1 className="team-name">Hackathon_Crew_Team_4</h1>
      <div className="messages-container" ref={messagesContainerRef}>
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}-message`}>
            {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-wrapper">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="텍스트를 입력하세요"
          className="text-input"
        />
        <button onClick={handleSend} className="send-button">보내기</button>
      </div>
    </div>
  )
}

export default App
