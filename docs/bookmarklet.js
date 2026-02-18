/**
 * LinkedIn Post Text Extractor Bookmarklet
 * 
 * Extracts text content from a LinkedIn post page, copies to clipboard,
 * and optionally sends to a webhook (Telegram bot, custom endpoint, etc.)
 * 
 * INSTALLATION:
 * 1. Create a new bookmark in your browser
 * 2. Set the name to "Extract LinkedIn Post"
 * 3. Set the URL to the minified version at the bottom of this file
 * 
 * USAGE:
 * 1. Navigate to a LinkedIn post page
 * 2. Click the bookmarklet
 * 3. Post text is copied to clipboard + shown in alert
 * 4. If WEBHOOK_URL is set, content is also sent there
 */

// ─── CONFIGURATION ────────────────────────────────────────────
// Set your webhook URL here (or leave empty for clipboard-only)
// For Telegram: https://api.telegram.org/bot<TOKEN>/sendMessage
const WEBHOOK_URL = '';
const TELEGRAM_CHAT_ID = '';  // Your Telegram chat ID (if using Telegram webhook)

// ─── FULL VERSION (for reading) ───────────────────────────────
(function() {
    'use strict';
    
    // LinkedIn DOM selectors — ordered by specificity/reliability
    // LinkedIn changes their DOM frequently; update these as needed
    const textSelectors = [
        '.feed-shared-update-v2__description',
        '.feed-shared-inline-show-more-text',
        '.update-components-text',
        '.feed-shared-update-v2__commentary',
        '.break-words .feed-shared-text',
        '[data-ad-preview="message"]',
        'article .break-words',
        // Single post view
        '.scaffold-finite-scroll__content .feed-shared-text',
    ];
    
    const authorSelectors = [
        '.update-components-actor__name .visually-hidden',
        '.feed-shared-actor__name',
        '.update-components-actor__title .visually-hidden',
    ];
    
    const headlineSelectors = [
        '.update-components-actor__description',
        '.feed-shared-actor__description',
    ];
    
    // ─── Extract content ──────────────────────────────────────
    function findText(selectors) {
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el && el.innerText.trim()) {
                return el.innerText.trim();
            }
        }
        return '';
    }
    
    // Try to click "...see more" to expand the post first
    const seeMore = document.querySelector('.feed-shared-inline-show-more-text button')
                 || document.querySelector('[data-control-name="see_more"]')
                 || document.querySelector('.see-more');
    if (seeMore) {
        seeMore.click();
        // Wait a moment for expansion
    }
    
    const text = findText(textSelectors);
    const author = findText(authorSelectors);
    const headline = findText(headlineSelectors);
    
    // Get any image URLs
    const images = [];
    document.querySelectorAll('.feed-shared-image__container img, .update-components-image img').forEach(img => {
        if (img.src && !img.src.includes('profile-displayphoto') && !img.src.includes('data:')) {
            images.push(img.src);
        }
    });
    
    // Get post URL
    const postUrl = window.location.href;
    
    if (!text) {
        alert('Could not find post text on this page.\n\nMake sure you\'re on a LinkedIn post.\nLinkedIn may have changed their DOM structure.');
        return;
    }
    
    // ─── Build output ─────────────────────────────────────────
    let output = '';
    if (author) output += `Author: ${author}\n`;
    if (headline) output += `${headline}\n`;
    if (author || headline) output += '\n';
    output += text;
    if (images.length) output += `\n\nImages: ${images.join('\n')}`;
    output += `\n\nSource: ${postUrl}`;
    
    // ─── Copy to clipboard ────────────────────────────────────
    navigator.clipboard.writeText(output).then(function() {
        const preview = output.substring(0, 400) + (output.length > 400 ? '...' : '');
        alert('✅ Copied to clipboard!\n\n' + preview);
    }).catch(function() {
        // Fallback: prompt for manual copy
        prompt('Copy this text:', output);
    });
    
    // ─── Send to webhook (optional) ───────────────────────────
    if (WEBHOOK_URL) {
        let body;
        
        if (WEBHOOK_URL.includes('api.telegram.org') && TELEGRAM_CHAT_ID) {
            // Telegram Bot API format
            body = JSON.stringify({
                chat_id: TELEGRAM_CHAT_ID,
                text: `📋 LinkedIn Post Extracted\n\n${output}`,
                parse_mode: 'Markdown',
            });
        } else {
            // Generic webhook
            body = JSON.stringify({
                source: 'linkedin-bookmarklet',
                url: postUrl,
                author: author,
                headline: headline,
                text: text,
                images: images,
                timestamp: new Date().toISOString(),
            });
        }
        
        fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body,
        }).then(r => {
            if (r.ok) console.log('Bookmarklet: sent to webhook');
            else console.warn('Bookmarklet: webhook returned', r.status);
        }).catch(e => {
            console.error('Bookmarklet: webhook failed', e);
        });
    }
})();

/*
 * ─── MINIFIED BOOKMARKLET ─────────────────────────────────────
 * 
 * Clipboard-only version (no webhook):
 * 
 * javascript:void((function(){'use strict';var ss=['.feed-shared-update-v2__description','.feed-shared-inline-show-more-text','.update-components-text','.feed-shared-update-v2__commentary','.break-words .feed-shared-text','[data-ad-preview="message"]','article .break-words'];function f(s){for(var i=0;i<s.length;i++){var e=document.querySelector(s[i]);if(e&&e.innerText.trim())return e.innerText.trim()}return''}var m=document.querySelector('.feed-shared-inline-show-more-text button');if(m)m.click();var t=f(ss),a=f(['.update-components-actor__name .visually-hidden','.feed-shared-actor__name']),h=f(['.update-components-actor__description']);if(!t){alert('No post text found on this page.');return}var o='';if(a)o+='Author: '+a+'\n';if(h)o+=h+'\n';if(a||h)o+='\n';o+=t+'\n\nSource: '+location.href;navigator.clipboard.writeText(o).then(function(){alert('✅ Copied!\n\n'+o.substring(0,400))}).catch(function(){prompt('Copy:',o)})})())
 * 
 * 
 * With Telegram webhook (replace TOKEN and CHAT_ID):
 * 
 * javascript:void((function(){'use strict';var W='https://api.telegram.org/botTOKEN/sendMessage',C='CHAT_ID';var ss=['.feed-shared-update-v2__description','.feed-shared-inline-show-more-text','.update-components-text','.feed-shared-update-v2__commentary','.break-words .feed-shared-text'];function f(s){for(var i=0;i<s.length;i++){var e=document.querySelector(s[i]);if(e&&e.innerText.trim())return e.innerText.trim()}return''}var m=document.querySelector('.feed-shared-inline-show-more-text button');if(m)m.click();var t=f(ss),a=f(['.update-components-actor__name .visually-hidden','.feed-shared-actor__name']);if(!t){alert('No text found');return}var o=(a?'Author: '+a+'\n\n':'')+t;navigator.clipboard.writeText(o).then(function(){alert('✅ Copied!')}).catch(function(){});fetch(W,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:C,text:'📋 LinkedIn:\n\n'+o})}).catch(function(){})})())
 */
