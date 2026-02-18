/**
 * LinkedIn Post Text Extractor Bookmarklet
 * 
 * Extracts post text from the current LinkedIn page and copies to clipboard.
 * 
 * Installation:
 * 1. Create a new bookmark in your browser
 * 2. Set the name to "Extract LinkedIn Post"
 * 3. Set the URL to the minified version below
 * 
 * Usage:
 * 1. Navigate to a LinkedIn post
 * 2. Click the bookmarklet
 * 3. Post text is copied to clipboard + shown in alert
 */

// Full version (for reading):
(function() {
    'use strict';
    
    // LinkedIn post text selectors (may need updating as LinkedIn changes DOM)
    const selectors = [
        '.feed-shared-update-v2__description',           // Feed posts
        '.feed-shared-inline-show-more-text',             // Expanded text
        '.break-words .feed-shared-text',                 // Alternative
        '[data-ad-preview="message"]',                    // Sponsored
        '.update-components-text',                        // Newer layout
        'article .break-words',                           // Article view
        '.feed-shared-update-v2__commentary',             // Commentary
    ];
    
    let text = '';
    
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText.trim()) {
            text = el.innerText.trim();
            break;
        }
    }
    
    // Also try to get author info
    const authorEl = document.querySelector('.update-components-actor__name .visually-hidden') 
                  || document.querySelector('.feed-shared-actor__name');
    const author = authorEl ? authorEl.innerText.trim() : '';
    
    if (!text) {
        alert('Could not find post text on this page. Make sure you\'re on a LinkedIn post.');
        return;
    }
    
    const output = author ? `Author: ${author}\n\n${text}` : text;
    
    // Copy to clipboard
    navigator.clipboard.writeText(output).then(function() {
        alert('Copied to clipboard!\n\n' + output.substring(0, 500) + (output.length > 500 ? '...' : ''));
    }).catch(function() {
        // Fallback: prompt for manual copy
        prompt('Copy this text:', output);
    });
})();

/*
 * Minified bookmarklet URL (paste as bookmark URL):
 * 
 * javascript:void((function(){var s=['.feed-shared-update-v2__description','.feed-shared-inline-show-more-text','.break-words .feed-shared-text','[data-ad-preview="message"]','.update-components-text','article .break-words','.feed-shared-update-v2__commentary'],t='',a='';for(var i=0;i<s.length;i++){var e=document.querySelector(s[i]);if(e&&e.innerText.trim()){t=e.innerText.trim();break}}var ae=document.querySelector('.update-components-actor__name .visually-hidden')||document.querySelector('.feed-shared-actor__name');if(ae)a=ae.innerText.trim();if(!t){alert('No post text found');return}var o=a?'Author: '+a+'\n\n'+t:t;navigator.clipboard.writeText(o).then(function(){alert('Copied!\n\n'+o.substring(0,500))}).catch(function(){prompt('Copy:',o)})})())
 */
