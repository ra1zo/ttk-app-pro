const express = require('express');
const multer = require('multer');
const fs = require('fs');
const cors = require('cors'); 
const { spawn } = require('child_process');
const app = express();
const port = 3001;

app.use(cors());
const processedFiles = new Set();
const STATE_DATA = {
    "TAMIL NADU": [
        {"StateCode": "33", "GSTType": "CGST/SGST", "VendorCode": "19206"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ],
    "WEST BENGAL": [
        {"StateCode": "19", "GSTType": "CGST/SGST", "VendorCode": "18786"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ],
    "MAHARASHTRA": [
        {"StateCode": "27", "GSTType": "CGST/SGST", "VendorCode": "18785"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ],
    "HARYANA": [
        {"StateCode": "06", "GSTType": "CGST/SGST", "VendorCode": "18787"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ],
    "KARNATAKA": [
        {"StateCode": "29", "GSTType": "CGST/SGST", "VendorCode": "51121"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ],
    "TELANGANA": [
        {"StateCode": "36", "GSTType": "CGST/SGST", "VendorCode": "21411"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ],
    "ASSAM": [
        {"StateCode": "18", "GSTType": "CGST/SGST", "VendorCode": "23531"},
        {"StateCode": "29", "GSTType": "IGST", "VendorCode": "51121"}
    ]
};


// Configure multer for file storage
const storage = multer.diskStorage({
    destination: function(req, file, cb) {
        cb(null, 'pdfFiles/'); // Make sure this directory exists
    },
    filename: function(req, file, cb) {
        cb(null, file.originalname);
    }
});
const upload = multer({ storage: storage });


app.post('/extract-text', upload.single('pdfFile'), (req, res) => {
    const pdfPath = req.file.path;
    const platform = req.body.platform.toLowerCase();
    const fileName = req.body.fileName;
    if (processedFiles.has(fileName)) {
        return res.status(500).send('Duplicate file tried to upload');
    }
    const pythonProcess = spawn('python3', [`python_core/${platform}.py`, pdfPath, fileName], {
        env: {
          ...process.env, // Include existing environment variables
          STATE_DATA: JSON.stringify(STATE_DATA), // Add your state data as an environment variable
        },
      });
    let extractedText = '';
    
    pythonProcess.stdout.on('data', (data) => {
        extractedText += data.toString();
        console.log(extractedText);
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });
  
    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.log('Deleting the PDF due to processing error...');
            fs.unlink(pdfPath, (err) => {
                if (err) console.error(`Failed to delete PDF: ${err}`);
            });
            return res.status(500).send('Error extracting text');
        }

        processedFiles.add(fileName);
        const generatedFilePath = __dirname + `/generated/${fileName}.csv`;

        // Check if the file exists before sending
        fs.access(generatedFilePath, fs.constants.F_OK, (err) => {
            if (err) {
                console.error(`Generated file not found: ${err}`);
                return res.status(404).send('Generated file not found');
            }
            console.log('Processing completed successfully, deleting the PDF...');
            fs.unlink(pdfPath, (unlinkErr) => {
                if (unlinkErr) {
                    console.error(`Failed to delete PDF: ${unlinkErr}`);
                }
                res.setHeader('Content-Disposition', `attachment; filename="${fileName}.xls"`);
                res.sendFile(generatedFilePath);
            });
        });
    });
});

app.get('/',(req,res)=>{
    console.log("Hello world");
    res.send('Working !!')
})

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});


