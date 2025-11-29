const puppeteer = require('puppeteer');
const fs = require('fs');
const csv = require('csv-parser');

(
    async () => {
        const browser = await puppeteer.launch({ headless: false });
        const mainPage = await browser.newPage()
        await mainPage.goto('https://i4replication.org/discussion_paper.html');

        await mainPage.waitForSelector("#reports-tab");
        await mainPage.click("#reports-tab");
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        await mainPage.waitForSelector('#economicsBtn');
        await mainPage.click('#economicsBtn');
        await new Promise(resolve => setTimeout(resolve, 1000));


        const articlesMetadata = await mainPage.evaluate(() => {
            const politicalScienceJournals = ["AJPS", "APSR", "JOP"];
            const humanBehaviorJournals = ["Nature Human Behaviour"];
            const economicsJournals = [
                "AE: Macro",
                "AEJ: Applied",
                "AEJ: Econ Policy",
                "AEJ: Macro",
                "AEJ: Policy",
                "AER",
                "AER: Insights",
                "EJ",
                "JPE",
                "QJE",
                "Restat",
                "Restud"
            ];

            function getFieldByJournal(journal) {
                if(economicsJournals.includes(journal)) {
                    return "Economics";
                } else if(politicalScienceJournals.includes(journal)) {
                    return "Political Science";
                } else if(humanBehaviorJournals.includes(journal)) {
                    return "Psychological Science";
                } else {
                    return null;
                }
            }


            const cards = document.querySelectorAll('#articles-container .col-md-6.mb-4');
            const metadata = [];

            cards.forEach(card => {
                const title = card.querySelector('h5.card-title')?.innerText.trim();
                const journal = card.querySelector('p.h6.text-secondary')?.innerText.trim();
                console.log(journal);
                const field = getFieldByJournal(journal);
                const year = null;
                const language = null;
                const links = null;
                metadata.push({ title, field, journal, year, language, links });
            });

            return metadata;
        });

        const paperLinks = await mainPage.evaluate(() => {
            return Array.from(document.querySelectorAll('#articles-container a')).map(a => a.href);
        });
        const paperPage = await browser.newPage()

        for(var i = 0; i < paperLinks.length; i++) {
            if(paperLinks[i] != 'https://example.com/article1') {
                await paperPage.goto(paperLinks[i], { waitUntil: 'networkidle2', timeout: 120000 });
                await new Promise(resolve => setTimeout(resolve, 4000));

                const links = await paperPage.evaluate(() => {
                    const span = document.querySelector('#nodeDescriptionEditable');
                    const anchors = span ? span.querySelectorAll('a') : [];
                        
                    return Array.from(anchors).map(a => a.href);
                });

                links.unshift(paperLinks[i]);

                await paperPage.goto(paperLinks[i] + 'metadata/osf',  { waitUntil: 'networkidle2', timeout: 120000 });
                await new Promise(resolve => setTimeout(resolve, 4000));

                const year = await paperPage.evaluate(() => {
                    const dateEl = document.querySelector('dd[data-test-creation-date]');
                    const dateText = dateEl ? dateEl.textContent.trim() : '';
                    const yearMatch = dateText.match(/\b(19|20)\d{2}\b/);
                    const year = yearMatch ? yearMatch[0] : '';

                    return year;
                });

                articlesMetadata[i].year = year;
                articlesMetadata[i].links = links.join(', ');
            }

            if(i % 20 == 0 && i > 0) {
                const headers = Object.keys(articlesMetadata[0]);
                const chunk = articlesMetadata.slice(i-20, i);
                const rows = chunk.map(obj =>
                    headers.map(header => `"${(obj[header] || '').replace(/"/g, '""')}"`).join(',')
                );
                const csvContent = [headers.join(','), ...rows].join('\n');
                fs.writeFileSync(`output/articlesMetadata_${i-19}_to_${i}.csv`, csvContent, 'utf8');
            }
        }


        const headers = Object.keys(articlesMetadata[0]);
        const rows = articlesMetadata.map(obj => headers.map(header => `"${(obj[header] || '').replace(/"/g, '""')}"`).join(','));
        const csvContent = [headers.join(','), ...rows].join('\n');
        fs.writeFileSync('output/articlesMetadata.csv', csvContent, 'utf8');

        const metadataFile = 'output/articlesMetadata.csv';
        const metaDatabaseFile = 'input/metadatabasePublic.csv';
        const outputFile = 'output/articlesData.csv';

        const metadataMap = new Map();
        const metaDatabaseMap = new Map();
        const metadataRows = [];

        fs.createReadStream(metadataFile)
        .pipe(csv())
        .on('data', row => {
            const title = row.title.trim();
            metadataMap.set(title, row);
            metadataRows.push(row);
        })
        .on('end', () => {
            fs.createReadStream(metaDatabaseFile)
            .pipe(csv())
            .on('data', row => {
                const title = row.title?.trim();
                
                if(title) {
                    metaDatabaseMap.set(title, row);
                }
            })
            .on('end', () => {
                const res = metadataRows.map(row => {
                const title = row.title.trim();
                const metaDatabaseByTitle = metaDatabaseMap.get(title);

                let perfect_reproduction = '';
                if(metaDatabaseByTitle?.perfect_reproduction) {
                    if(metaDatabaseByTitle.perfect_reproduction.trim().toLowerCase() == 'yes') {
                        perfect_reproduction = '1';
                    } else if(metaDatabaseByTitle.perfect_reproduction.trim().toLowerCase() == 'no') {
                        perfect_reproduction = '0';
                    }
                }

                return {
                    ...row,
                    computational_reproduction: metaDatabaseByTitle?.computational_reproduction || '',
                    perfect_reproduction: perfect_reproduction,
                    comments: metaDatabaseByTitle?.comments || ''
                };
                });

                const headers = Object.keys(res[0]);
                const csvContent = [
                    headers.join(','),
                    ...res.map(row =>
                        headers.map(h => `"${(row[h] || '').replace(/"/g, '""')}"`).join(',')
                    )
                ].join('\n');

                fs.writeFileSync(outputFile, csvContent, 'utf8');
            });
        });


        

        await browser.close();
    }
)();