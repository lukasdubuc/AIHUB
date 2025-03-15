
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';git add .
  
git commit -m "Initial commit"
git push -u origin main

dotenv.config();

const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Server is running' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});
