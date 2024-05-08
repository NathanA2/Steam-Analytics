import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import './App.css';

function App() {
  const [steamId, setSteamId] = useState('');
  const [recentGames, setRecentGames] = useState([]);
  const [allGames, setAllGames] = useState([]);

  const fetchRecentGames = () => {
    fetch(`http://localhost:5000/steam/recently_played/${steamId}`)
      .then(response => response.json())
      .then(data => setRecentGames(data))
      .catch(error => console.error('Error fetching recent games:', error));
  };

  const fetchAllGamesGenres = () => {
    fetch(`http://localhost:5000/steam/all_games_genres/${steamId}`)
      .then(response => response.json())
      .then(data => setAllGames(data))
      .catch(error => console.error('Error fetching all games genres:', error));
  };

  // Prepare data for the pie chart based on playtime per genre in hours
  const genreData = allGames.reduce((acc, game) => {
    game.genres.forEach(genre => {
      const found = acc.find(item => item.name === genre);
      if (found) {
        found.value += game.playtime_forever / 60; // Convert minutes to hours and sum up the playtime
      } else {
        acc.push({ name: genre, value: game.playtime_forever / 60 }); // Initialize with the first playtime converted to hours
      }
    });
    return acc;
  }, []);

  // Sort genre data by descending playtime
  genreData.sort((a, b) => b.value - a.value);

  const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#9900FF', // Original colors
    '#E6194B', '#3CB44B', '#FFE119', '#4363D8', '#F58231', // Additional vibrant colors
    '#911EB4', '#46F0F0', '#F032E6', '#BCF60C', '#FABEBE', // More distinct colors
    '#008080', '#E6BEFF', '#9A6324', '#FFFAC8', '#800000'  // More distinct colors
  ];

  useEffect(() => {
    if (steamId) {
      fetchRecentGames();
      fetchAllGamesGenres();
    }
  }, [steamId]);  // Fetch data when steamId changes

  return (
    <div className="App">
      <header className="App-header">
        <input
          type="text"
          value={steamId}
          onChange={e => setSteamId(e.target.value)}
          placeholder="Enter Steam ID"
        />
        <button onClick={() => { fetchRecentGames(); fetchAllGamesGenres(); }}>Fetch Games</button>
        <h2>Recently Played Games</h2>
        <ul>
          {recentGames.map(game => (
            <li key={game.appid}>{game.name} - played {game.playtime_2weeks} minutes in last 2 weeks</li>
          ))}
        </ul>
        <h2>Genre Distribution by Playtime</h2>
        <div className="PieChart-container">
          <PieChart width={400} height={400}>
            <Pie dataKey="value" isAnimationActive={true} data={genreData} cx={200} cy={200} outerRadius={180} fill="#8884d8">
              {genreData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [`${value.toFixed(2)} hours`, `Genre: ${name}`]} />
          </PieChart>
        </div>
      </header>
    </div>
  );
}

export default App;