import { useNavigate } from 'react-router'
import { useState, useEffect } from 'react';


export default function Settings() {
  const navigate = useNavigate()

  return (
    <button className="w-[74px] h-[74px] rounded-full flex items-center justify-center mb-4 animate-pulse-ring bg-red-100 text-white cursor-pointer" onClick={() => navigate('/home')}>Home</button>
)
}
