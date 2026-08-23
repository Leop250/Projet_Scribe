export const SOURCE_ICON = { dictaphone: '●', visio: '◆' }
export const SOURCE_LABEL = { dictaphone: 'Dictaphone', visio: 'Visio' }
export const SOURCE_COLOR = { dictaphone: '#ff2e00', visio: '#1a56ff' }

export function displaySource(source) {
  return source === 'calendar' ? 'visio' : source
}
