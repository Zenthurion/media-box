import play from 'play-dl';

export type MediaType = 'youtube-music' | 'youtube-video' | 'invalid';

const supportedDomains = {
  'youtube.com': true,
  'youtu.be': true,
  'music.youtube.com': true
};

export async function identifyUrl(url: string): Promise<MediaType> {
  const mediaType = determineMediaType(url);
  const validationResult = await play.validate(url);

  if(!validationResult)
    return 'invalid';

  return mediaType;
}

function determineMediaType(url: string): MediaType {
  const urlObj = new URL(url);

  if (!supportedDomains[urlObj.hostname as keyof typeof supportedDomains]) {
    return 'invalid';
  }

  if (urlObj.hostname === 'music.youtube.com' || (urlObj.hostname === 'youtube.com' && urlObj.searchParams.get('list'))) {
    return 'youtube-music';
  }

  return 'youtube-video';
}
