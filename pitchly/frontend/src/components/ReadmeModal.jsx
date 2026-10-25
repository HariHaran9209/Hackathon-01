import React, { useState, useEffect } from 'react';
import styles from './ReadmeModal.module.css';

export default function ReadmeModal({ isOpen, onClose, projectId, api }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && projectId) {
      setLoading(true);
      api
        .getProjectReadme(projectId)
        .then((res) => {
          setContent(res.readme || '');
        })
        .catch((err) => {
          setContent(`Failed to load README: ${err.message}`);
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, projectId]);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `README-project-${projectId}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.titleArea}>
            <span className={styles.title}>Project README.md</span>
          </div>

          <div className={styles.actions}>
            <button
              className={`${styles.copyButton} ${copied ? styles.copiedSuccess : ''}`}
              onClick={handleCopy}
              disabled={loading}
            >
              {copied ? '✓ Copied!' : 'Copy Markdown'}
            </button>

            <button
              className={styles.downloadButton}
              onClick={handleDownload}
              disabled={loading}
            >
              Download .md
            </button>

            <button className={styles.closeButton} onClick={onClose} title="Close modal">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <div className={styles.modalBody}>
          {loading ? (
            <div style={{ color: '#8b949e', textAlign: 'center', padding: '40px' }}>
              Generating Markdown documentation...
            </div>
          ) : (
            <pre className={styles.markdownPre}>{content}</pre>
          )}
        </div>
      </div>
    </div>
  );
}
