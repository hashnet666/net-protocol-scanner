document.addEventListener('DOMContentLoaded', function() {
    // ... (previous variable declarations remain the same)
    
    function handleScanCompletion(data) {
        successfulHosts = data.results || [];
        const successful101Hosts = data.results_101 || [];
        
        output.innerHTML += `\n<span class="success">> Scan completed. ${successfulHosts.length} successful, ${data.failed || 0} failed.</span>`;
        output.innerHTML += `\n<span class="success">> ${successful101Hosts.length} hosts with 101 Switching Protocols detected.</span>`;
        // REMOVED: Email notification message - users don't see this
        
        // Show ALL successful hosts to user (both regular and 101)
        const allSuccessfulHosts = [...new Set([...successfulHosts, ...successful101Hosts])];
        
        if (allSuccessfulHosts.length > 0) {
            resultsContent.textContent = allSuccessfulHosts.join('\n');
            resultsSection.style.display = 'block';
            
            if (successful101Hosts.length > 0) {
                output.innerHTML += `\n<span class="success">> ⚡ ${successful101Hosts.length} hosts with 101 Switching Protocols found!</span>`;
                output.innerHTML += `\n<span class="success">> ✅ ${successfulHosts.length - successful101Hosts.length} other successful hosts found.</span>`;
                output.innerHTML += `\n<span class="info">> All ${allSuccessfulHosts.length} successful hosts shown below - Ready to copy!</span>`;
            } else {
                output.innerHTML += `\n<span class="success">> All ${allSuccessfulHosts.length} successful hosts shown below - Ready to copy!</span>`;
            }
            
            // Auto-copy ALL successful hosts to clipboard
            copyResultsToClipboard(allSuccessfulHosts);
        } else {
            output.innerHTML += `\n<span class="warning">> No successful hosts found.</span>`;
        }
        
        isScanning = false;
        updateUIForScanning(false);
    }

    function updateScanProgress(data) {
        if (data.processed !== undefined && data.total > 0) {
            const progress = Math.round((data.processed / data.total) * 100);
            progressEl.textContent = `${progress}%`;
            successHostsEl.textContent = data.successful || 0;
            failedHostsEl.textContent = data.failed || 0;
            
            // Show 101 hosts in the output if available
            if (data.successful_101 > 0) {
                output.innerHTML += `\n<span class="success">> 101 Switching Protocols: ${data.successful_101} hosts found so far</span>`;
            }
            
            if (data.processed % 10 === 0) {
                output.innerHTML += `\n<span class="info">> Progress: ${data.processed}/${data.total} hosts (${progress}%)</span>`;
                output.scrollTop = output.scrollHeight;
            }
        }
    }

    async function copyResultsToClipboard(hosts) {
        try {
            await navigator.clipboard.writeText(hosts.join('\n'));
            output.innerHTML += `\n<span class="success">> ✅ All ${hosts.length} successful hosts copied to clipboard automatically!</span>`;
        } catch (err) {
            output.innerHTML += `\n<span class="warning">> Failed to auto-copy results: ${err}</span>`;
        }
    }

    // Update the copy button to copy ALL successful hosts
    async function copyResults() {
        try {
            const allHosts = resultsContent.textContent.split('\n').filter(host => host.trim());
            await navigator.clipboard.writeText(allHosts.join('\n'));
            output.innerHTML += `\n<span class="success">> ✅ All ${allHosts.length} hosts copied to clipboard!</span>`;
        } catch (err) {
            output.innerHTML += `\n<span class="error">> Failed to copy results: ${err}</span>`;
        }
    }

    // ... rest of your JavaScript functions remain the same
});