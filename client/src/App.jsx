import { useState } from 'react';
import axios from 'axios'; 
import './App.css';
import logo from './assets/logo.jpg';

function App() {
  const [file, setFile] = useState(null);
  const [platform, setPlatform] = useState('');
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');

  const validateFileAndPlatform = (file, platform) => {
    if (!file || !platform) return false; // Ensure both file and platform are selected
    const fileName = file.name.toLowerCase();
    const platformLower = platform.toLowerCase();
    return fileName.includes(platformLower);
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile.type !== 'application/pdf') {
      setError('Please upload only PDF files.');
      setFile(null);
    } else {
      setError('');
      setFile(selectedFile);
      // Validate filename and platform match right after file selection
      if (!validateFileAndPlatform(selectedFile, platform)) {
        setError('Choose correct vendor.');
      } else {
        setError('');
      }
    }
  };

  const handlePlatformChange = (value) => {
    setPlatform(value);
    // Validate filename and platform match right after platform selection
    if (!validateFileAndPlatform(file, value)) {
      setError('Choose correct vendor.');
    } else {
      setError('');
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || !platform) {
      setError('Please fill all fields correctly.');
      return;
    }
  const fileName = file.name.replace(/\.[^/.]+$/, "");
  const formData = new FormData();
  formData.append('pdfFile', file);
  formData.append('platform', platform);
  formData.append('fileName', fileName);

    try {
      const response = await axios.post('https://ttk-app-backend.onrender.com/extract-text', formData, {
        responseType: 'blob', // Important for downloading files
      });
      if (response.status === 200) {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${fileName}.csv`);
        document.body.appendChild(link);
        link.click();
        setResponse('File processed successfully.');
      }
    } catch (error) {
      console.log(error);
      if (error.response) {
          error.response.data.text().then(text => {
          setError(text);
        });
      } else {
        setError('An error occurred while sending the request.');
      }
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <img src={logo} className="app-logo" alt="TTK-APP Logo" />
        <h1 className="app-title">TTK-APP</h1>
      </header>
      {error && <p className="error-message">{error}</p>}
      {response && <p className="success-message">{response}</p>}
      <form onSubmit={handleSubmit} className="upload-form">
        <input type="file" onChange={handleFileChange} required />
        <div className="radio-buttons">
          <input type="radio" id="amazon" name="platform" value="Amazon" onChange={(e) => handlePlatformChange(e.target.value)} />
          <label htmlFor="amazon">Amazon</label>
          <input type="radio" id="flipkart" name="platform" value="Flipkart" onChange={(e) => handlePlatformChange(e.target.value)} />
          <label htmlFor="flipkart">Flipkart</label>
        </div>
        <button type="submit" disabled={!!error} className="submit-button">Submit</button>
      </form>
      <footer className="app-footer">
        Developed by Prakash
      </footer>
    </div>
  );
}

export default App;