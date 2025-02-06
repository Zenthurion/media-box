export class URLHandler {
    private supportedDomains = {
      'youtube.com': true,
      'youtu.be': true,
      'music.youtube.com': true
    };
  
    async determineMediaType(url: string): Promise<string> {
      const urlObj = new URL(url);
      
      if (!this.supportedDomains[urlObj.hostname as keyof typeof this.supportedDomains]) {
        throw new Error('Unsupported domain');
      }
  
      if (urlObj.hostname === 'music.youtube.com' || 
          (urlObj.hostname === 'youtube.com' && urlObj.searchParams.get('list'))) {
        return 'youtube-music';
      }
  
      return 'youtube-video';
    }
  }