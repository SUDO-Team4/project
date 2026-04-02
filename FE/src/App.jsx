import { useState } from 'react'
import logo from './assets/Group 11.svg'
import './App.css'

function App() {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (input.trim()) {
      console.log('보내기:', input)
      setInput('')
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
