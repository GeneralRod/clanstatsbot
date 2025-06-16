const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Helper functie voor delay
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
    // Get the current week's data using environment variable
    const currentWeek = process.env.CURRENT_WEEK || '25'; // Fallback to 25 if not set
    const currentWeekPath = path.resolve(__dirname, `../data/week${currentWeek}.json`);
    const currentData = JSON.parse(fs.readFileSync(currentWeekPath, 'utf-8'));

    // Debug logging
    console.log('\n=== DEBUG: Rendering Leaderboard ===');
    console.log('Current week:', currentWeek);
    console.log('Number of players:', currentData.length);
    console.log('\nFirst few players:');
    currentData.slice(0, 3).forEach(player => {
        console.log(`\nPlayer: ${player.name}`);
        console.log(`  Rating: ${player.rating}`);
        console.log(`  Rating diff: ${player.rating_diff}`);
        console.log(`  User ID: ${player.user_id}`);
    });

    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Correct pad naar template.html
    const templatePath = path.resolve(__dirname, 'template.html');
    await page.goto(`file://${templatePath}`);

    // Wacht tot de tabel is geladen
    await page.waitForSelector('table');

    await page.evaluate((data) => {
        const tbody = document.querySelector("tbody");
        data.forEach((player, index) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${player.name}</td>
                <td>${player.rating} <span style='color: ${player.rating_diff >= 0 ? "lime" : "red"}'>(${player.rating_diff >= 0 ? "+" : ""}${player.rating_diff})</span></td>
                <td>${player.peak}</td>
                <td>${player.wins}</td>
                <td>${player.games}</td>
            `;
            tbody.appendChild(row);
        });
    }, currentData);

    // Wacht even om er zeker van te zijn dat alle rijen zijn gerenderd
    await delay(1000);

    // Screenshot in output folder, relatief aan src
    const screenshotPath = path.resolve(__dirname, '../output/leaderboard.png');
    
    // Pas de viewport aan aan de inhoud
    const bodyHandle = await page.$('body');
    const { width, height } = await bodyHandle.boundingBox();
    await page.setViewport({
        width: Math.ceil(width),
        height: Math.ceil(height),
        deviceScaleFactor: 1
    });

    // Maak de screenshot met de juiste opties
    await page.screenshot({
        path: screenshotPath,
        fullPage: true,
        omitBackground: true
    });

    console.log('\n=== Rendering Complete ===');
    console.log(`Screenshot saved to: ${screenshotPath}`);

    await browser.close();
})(); 